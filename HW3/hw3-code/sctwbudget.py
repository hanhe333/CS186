#!/usr/bin/env python

import sys,math

from gsp import GSP
from util import argmax_index

class Sctwbudget:
    """Balanced bidding agent"""
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget
        self.total_spent = 0
        self.remaining = budget
        self.roundsPerDay = 48

    def initial_bid(self, reserve):
        return self.value / 2


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

        prev_round = history.round(t-1)
        clicks = prev_round.clicks
        info = self.slot_info(t, history, reserve)

        utilities = [None]*len(clicks)
        for i in range(0,len(clicks)):
            utilities[i] =  clicks[i]*(self.value - info[i][1])

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
        prev_round = history.round(t-1)
        clicks = prev_round.clicks

        try:
            slot = prev_round.occupants.index(self.id)
        except ValueError:
            slot = -1
        if slot != -1:
            prev_spend = prev_round.slot_payments[slot]
            self.total_spent += prev_spend
            self.remaining -= prev_spend

        (slot, min_bid, max_bid) = self.target_slot(t, history, reserve)

        # During low click, instead of max utility, try to save money
        if t > 22 and t < 26:
            slot = min(slot - 1, len(clicks) - 1)

        if min_bid >= self.value:
            bid = self.value
        elif slot > 0:
            # print self.value, clicks[slot], min_bid, clicks[slot-1], clicks[slot]*(self.value - min_bid) / clicks[slot-1]
            bid = int(self.value - clicks[slot]*(self.value - min_bid) / float(clicks[slot-1]))
        else:
            bid = self.value

        # If the bid will prevent us from bidding at least the reserve for the rest of day:
        # reduce the bid to reserve price
        # (We want to be able to participate in every bidding)
        if (self.remaining - bid) < reserve * (self.roundsPerDay - t):
            bid = reserve
        
        #print "budget =", self.remaining, "=", self.budget, "-", self.total_spent
        
        return bid

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)


