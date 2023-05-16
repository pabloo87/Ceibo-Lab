import math

import tkinter as tk

from card import Card

from tkinter import ttk
from config import SECONDARY_BG


class Footer(tk.Frame):
    def __init__(self, parent, *args, **kwargs) -> None:
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.config(width=600, height=0, background=SECONDARY_BG, padx=10, pady=10)

        self.cards = []
        self.index_selected = None
        self.event_trigger = None

        self.pack(side=tk.BOTTOM, fill=tk.X)

    def is_card_loaded(self):
        return len(self.cards) > 0
    
    def on_card_selected(self, fn):
        # Event triggered on every card click
        self.event_trigger = fn

    def create_card(self, filepath: str, index=None) -> None:
        if index is None:
            index = len(self.cards)

        card = Card(self, filepath, index)
        card.bind('<Button-1>', lambda _, c=card: self.event_trigger(c))
        self.cards.append(card)

    def select_card_by_index(self, index: int) -> Card:
        # Deselect selected card
        if len(self.cards) == 0:
            return

        if self.index_selected is not None:
            self.cards[self.index_selected].toggle_border()

        # select new, update index and return selected thumbnail
        self.cards[index].toggle_border()
        self.index_selected = index
        return self.cards[index]

    def on_footer_change(self, fn):
        self.bind('<Configure>', fn)

    def current_card_index(self) -> int:
        return self.index_selected
    
    def update_card(self, card: Card, index: int) -> None:
        self.cards[index] = card
    
    def get_current_card(self) -> Card:
        return self.cards[self.index_selected]

    def remove_card_by_index(self, index: int) -> None:
        self.cards[index].grid_forget()
        del self.cards[index]

        if index == self.index_selected:
            self.index_selected = None

        if len(self.cards) == 0:
            # Reset footer config to hide it
            self.config(width=600, height=0, background=SECONDARY_BG, padx=10, pady=10)
        else:
            # Reassing indexes
            for i, card in enumerate(self.cards):
                card.index = i
            self.update_grid()

    def update_grid(self):
        """
        Thumbnails are sort as follow:
         0 1 2
         3 4 5
         6 7 8
        """
        w = self.winfo_width()
        num_cols = max(math.floor(w / 400), 1)
        
        for i, card in enumerate(self.cards):
            card.grid(row=math.floor(i / num_cols), column=i % num_cols, sticky='w')
