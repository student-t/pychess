from gi.repository import Gtk

from pychess.Utils.const import UNDOABLE_STATES
from pychess.Utils.Cord import Cord
from pychess.Utils.logic import getStatus
from pychess.perspectives.learn.PuzzlesPanel import start_puzzle_from
from pychess.perspectives.learn.EndgamesPanel import start_endgame_from

HINT, MOVE, RETRY, NEXT = 0, 1, 2, 3


class LearnInfoBar(Gtk.InfoBar):
    def __init__(self, gamemodel, boardview):
        Gtk.InfoBar.__init__(self)

        self.content_area = self.get_content_area()
        self.action_area = self.get_action_area()

        self.gamemodel = gamemodel
        self.boardview = boardview
        self.shown_board = None

        self.gamemodel.connect("game_changed", self.game_changed)
        self.connect("response", self.on_response)

        self.your_turn()

    def clear(self):
        for item in self.content_area:
            self.content_area.remove(item)

        for item in self.action_area:
            self.action_area.remove(item)

    def your_turn(self, shown_board=None):
        if shown_board is not None:
            self.shown_board = shown_board

        self.clear()
        self.set_message_type(Gtk.MessageType.QUESTION)
        self.content_area.add(Gtk.Label(_("Your turn.")))
        self.add_button(_("Hint"), HINT)
        self.add_button(_("Move"), MOVE)
        self.show_all()

    def get_next_puzzle(self):
        self.clear()
        self.set_message_type(Gtk.MessageType.INFO)
        self.content_area.add(Gtk.Label(_("Well done!")))
        self.add_button(_("Next"), NEXT)
        self.show_all()

    def retry(self, shown_board=None):
        if shown_board is not None:
            self.shown_board = shown_board

        self.clear()
        self.set_message_type(Gtk.MessageType.ERROR)
        self.content_area.add(Gtk.Label(_("Not the best!")))
        self.add_button(_("Retry"), RETRY)

        # disable retry button until engine thinking on next move
        if self.gamemodel.practice_game:
            self.set_response_sensitive(RETRY, False)
        self.show_all()

    def on_response(self, widget, response):
        if response in (HINT, MOVE):
            if self.gamemodel.hint:
                if self.boardview.arrows:
                    self.boardview.arrows.clear()
                if self.boardview.circles:
                    self.boardview.circles.clear()

                hint = self.gamemodel.hint
                cord0 = Cord(hint[0], int(hint[1]), "G")
                cord1 = Cord(hint[2], int(hint[3]), "G")
                if response == HINT:
                    self.boardview.circles.add(cord0)
                    self.boardview.redrawCanvas()
                else:
                    self.boardview.arrows.add((cord0, cord1))
                    self.boardview.redrawCanvas()
            else:
                print("No hint available!")

        elif response == RETRY:
            if self.gamemodel.practice_game:
                self.gamemodel.undoMoves(2)
            elif self.gamemodel.lesson_game:
                self.boardview.setShownBoard(self.shown_board)
            self.your_turn()

        elif response == NEXT:
            if self.gamemodel.practice_game:
                if self.gamemodel.practice[0] == "puzzle":
                    start_puzzle_from(self.gamemodel.practice[1])
                elif self.gamemodel.practice[0] == "endgame":
                    start_endgame_from(self.gamemodel.practice[1])
            else:
                print("Next clicked!")

    def game_changed(self, gamemodel, ply):
        if gamemodel.practice_game:
            if len(gamemodel.moves) % 2 == 0:
                # engine moved, we can enable retry
                self.set_response_sensitive(RETRY, True)
                return

            # print(gamemodel.hint, repr(gamemodel.moves[-1]))
            status, reason = getStatus(gamemodel.boards[-1])

            if status in UNDOABLE_STATES:
                self.get_next_puzzle()
            elif gamemodel.hint and gamemodel.hint != repr(gamemodel.moves[-1]):
                self.retry()
            else:
                self.your_turn()
