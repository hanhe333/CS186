#!/usr/bin/env python

import sys
from auction import iround
import math
from gsp import GSP
from util import argmax_index

class HHAWbudget:
    """Balanced bidding agent"""
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget
        self.TOTAL_CLICKS = 0
        self.NUMBER_OF_PLAYERS = 0
        self.NUMBER_OF_SLOTS = 0

    def initialize_parameters(self, t, history):
        num_slots = len(history.round(t-1).clicks)

        self.NUMBER_OF_SLOTS = num_slots

        total_clicks = 0
        for time in range(48):
            total_clicks += self.clicks_round(time)

        self.TOTAL_CLICKS = total_clicks

        self.NUMBER_OF_PLAYERS = len(history.round(t-1).bids)

    def clicks_round(self, t):
        clicks = 0.0
        for slot in range(self.NUMBER_OF_SLOTS):
            clicks += self.clicks_slot(t, slot)

        return clicks

    def clicks_slot(self, t, slot):
        return iround(iround(30*math.cos(math.pi*t/24) + 50)*(.75**slot))

    def clicks_factor(self, t):
        return (self.clicks_round(t)/(self.TOTAL_CLICKS/48))**(.33)

    def calculate_past_clicks(self, t, history):
        past_clicks = 0
        for i in range(t-1):
            past_clicks += sum(history.round(i).clicks)
        return past_clicks

    def calculate_budgets(self, t, history):
       # sorted from lowest bid to highest
       id_to_budget = dict()

       ids = list()
       for i in xrange(len(history.round(t-1).bids)):
           ids.append(history.round(t-1).bids[i][0])

       for idx in ids:
           for i in xrange(t):
               bids = sorted(history.round(i).bids, key=lambda bid: -bid[1])
               slot_num = -1
               for j in xrange(len(bids)-1):
                   if bids[j][0] == idx and j < len(history.round(i).slot_payments):
                       slot_num = j
               if not idx in id_to_budget:
                   id_to_budget[idx] = 0
               if slot_num != -1:
                   id_to_budget[idx] = id_to_budget[idx] + history.round(i).slot_payments[slot_num]

       return id_to_budget

    def defaults(self, t, history, reserve):
        num_zero = 0

        if t < 2:
            return 0
        else:
            for i in xrange(self.NUMBER_OF_PLAYERS):
                if history.round(t-2).bids[i][1] <= reserve+1 and history.round(t-1).bids[i][1] <= reserve+1 and i != self.id:
                    num_zero += 1
                elif history.round(t-1).bids[i][1] <= reserve+1 and i != self.id:
                    num_zero += .5

        return num_zero

    def budget_factor(self, t, history, reserve):
        budget = self.calculate_budgets(t, history)[self.id]
        past_clicks = self.calculate_past_clicks(t, history)
        defaults = self.defaults(t, history, reserve)

        budget_value = (1.0 - (budget/60000.0) + (float(past_clicks)/self.TOTAL_CLICKS))**2.5

        if budget_value < .7 and defaults >= .5:
            return 0
        elif budget_value < .8 and defaults >= 1:
            return 0
        elif budget_value < .85 and defaults >= 1.5 and t < 47:
            return 0

        return budget_value

        
    def slot_info(self, t, history, reserve):
        """Compute the following for each slot, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns list of tuples [(slot_id, min_bid, max_bid)], where
        min_bid is the bid needed to tie the other-agent bid for that slot
        in the last round.  If slot_id = 0, max_bid is 2* min_bid.
        Otherwise, it's the next highest min_bid (so bidding between min_bid
        and max_bid would result in ending up in that slot)
        """
        prev_round = history.round(t-1)
        avr_round = []

        if t >= 2:
            prev_round2 = history.round(t-2)

            # predict other people's values
            for i in xrange(len(prev_round.bids)):
                if prev_round.bids[i][1] == 0:
                    avr_round.append(prev_round.bids[i])                       
                elif abs(prev_round.bids[i][1] - prev_round2.bids[i][1]) < 10:
                    avr_round.append((prev_round.bids[i][0], .5*prev_round.bids[i][1] + .5*prev_round2.bids[i][1]))
                else:
                    avr_round.append(prev_round2.bids[i])
        else:
            avr_round = prev_round.bids

        other_bids = filter(lambda (a_id, b): a_id != self.id, avr_round)

        clicks = prev_round.clicks
        def compute(s):
            (min, max) = GSP.bid_range_for_slot(s, clicks, reserve, other_bids)
            if max == None:
                max = 2 * min
            return (s, min, max)
            
        info = map(compute, range(len(clicks)))
#        sys.stdout.write("slot info: %s\n" % info)
        return info

    
    def expected_utils(self, t, history, reserve):
        """
        Figure out the expected utility of bidding such that we win each
        slot, assuming that everyone else keeps their bids constant from
        the previous round.

        returns a list of utilities per slot.
        """
        # TODO: Fill this in
        clicks = history.round(t-1).clicks
        utilities = [0.0]*(len(clicks))   # Change this

        info = self.slot_info(t, history, reserve)

        for i in xrange(len(clicks)):
            s_k = self.clicks_slot(t, i)
            utilities[i] = s_k*(self.value - info[i][1])
        
        return utilities

    def target_slot(self, t, history, reserve):
        """Figure out the best slot to target, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns (slot_id, min_bid, max_bid), where min_bid is the bid needed to tie
        the other-agent bid for that slot in the last round.  If slot_id = 0,
        max_bid is min_bid * 2
        """
        i =  argmax_index(self.expected_utils(t, history, reserve))
        info = self.slot_info(t, history, reserve)
        return info[i]

    def initial_bid(self, reserve):
        bid = 0
        if self.value <=60:
           return self.value-.01
        else:
            return .55*self.value-.01

    def bid(self, t, history, reserve):
        # The Balanced bidding strategy (BB) is the strategy for a player j that, given
        # bids b_{-j},
        # - targets the slot s*_j which maximizes his utility, that is,
        # s*_j = argmax_s {clicks_s (v_j - p_s(j))}.
        # - chooses his bid b' for the next round so as to
        # satisfy the following equation:
        # clicks_{s*_j} (v_j - p_{s*_j}(j)) = clicks_{s*_j-1}(v_j - b')
        # (p_x is the price/click in slot x)
        # If s*_j is the top slot, we (arbitrarily) choose
        #        b' = (v_j + p_0(j)) / 2. We can 
        # thus deal with all slots uniformly by defining clicks_{-1} = 2 clicks_0.
        #

        # initialize parameters
        if self.NUMBER_OF_PLAYERS == 0 or self.TOTAL_CLICKS == 0 or self.NUMBER_OF_SLOTS == 0:
            self.initialize_parameters(t, history)
            # print "Number of players: ", self.NUMBER_OF_PLAYERS
            # print "Number of slots: ", self.NUMBER_OF_SLOTS
            # print "Total clicks", self.TOTAL_CLICKS

        prev_round = history.round(t-1)
        
        (slot, min_bid, max_bid) = self.target_slot(t, history, reserve)

        num_default = self.defaults(t, history, reserve)

        bid = 0
        if num_default == 0:
            bid = (min_bid + max_bid)/2
        elif num_default > 0 and num_default <= 1:
            bid = (.25*min_bid + .75*max_bid)
        elif num_default > 1:
            bid = max_bid

        budget_effect = self.budget_factor(t, history, reserve)
        click_effect = self.clicks_factor(t)

        # print "defaults: ", num_default
        # print "bid (pre factors): ", bid, min_bid, max_bid
        # print "slot: ", slot
        # print "budget: ", budget_effect
        # print "click: ", click_effect
  
        bid = bid*budget_effect*click_effect

        if bid > max_bid:
            bid = max_bid

        if bid > self.value:
            bid = self.value
        if bid < reserve+1.01 and reserve+1.01 < self.value:
            return reserve+1.01

        if self.value < 75 and budget_effect > 1:
            return self.value

        return iround(bid)-0.01

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)


