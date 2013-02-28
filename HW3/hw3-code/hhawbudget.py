#!/usr/bin/env python

import sys
from auction import iround
import math
from gsp import GSP
from util import argmax_index

class HHAWbudget:
    TOTAL_CLICKS = 0
    """Balanced bidding agent"""
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget
        self.number_of_players

    def calculate_total_clicks(self, t, history):
        num_slots = len(history.round(t-1).bids)-1
        if num_slots == 3:
            TOTAL_CLICKS = 5376
        elif num_slots == 4:
            TOTAL_CLICKS = 6352
        elif num_slots == 5: 
            TOTAL_CLICKS = 7084
        elif num_slots == 6: 
            TOTAL_CLICKS = 7637

    def calculate_past_clicks(self, t, history):
        past_clicks = 0
        for i in range(t-1):
            past_clicks += sum(history.round(t).clicks)
        return past_clicks

    # set all budgets equal
    def initialize_budget(self, t, history):
        prev_round = history.round(t-1)
        for bid in prev_round.bids:
            self.budget[bid[0]] = self.budget[self.id]

    def calculate_budgets(self, t, history):
       # sorted from lowest bid to highest
       id_to_budget = dict()

       ids = list()
       for i in xrange(history.round(t-1).bids):
           ids.append(history.round(t-1).bids[i][0])

       for idx in ids:
           for i in xrange(t):
               bids = sorted(history.round(i).bids, key=lambda bid: bid[1])
               slot_num = -1
               for j in xrange(bids):
                   if bids[j][0] == idx:
                       slot_num = j
               if not idx in id_to_budget:
                   id_to_buget[idx] = 0
               if slot_num != -1:
                   id_to_budget[idx] = id_to_budget[idx] + history.round(i).slot_payments[slot_num]

       return id_to_budget
        
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
        other_bids = filter(lambda (a_id, b): a_id != self.id, prev_round.bids)

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
            s_k = clicks[i]
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
        return self.value

    def clicks_round(self, t):
        clicks = 0.0
        for i in range(self.number_of_players-1):
            clicks += iround(iround(30*math.cos(math.pi*t/24) + 50)*(.75**i))

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

        # click ratio
        prev_round = history.round(t-1)
        
        clicks = 0.0
        for i in range(4):
            clicks += iround(iround(30*math.cos(math.pi*t/24) + 50)*(.75**i))

        click_ratio = clicks/219.0

        # our budget


        
        return 0

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)


