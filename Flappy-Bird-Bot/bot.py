import pyglet
import random
import pickle
import atexit
import os
from pybird.game import Game


class Bot:
    def __init__(self, game):
        self.game = game
        # constants
        self.WINDOW_HEIGHT = Game.WINDOW_HEIGHT
        self.PIPE_WIDTH = Game.PIPE_WIDTH
        # this flag is used to make sure at most one tap during
        # every call of run()
        self.tapped = False

        self.game.play()

        # variables for plan
        self.Q = {}
        self.alpha = 0.6
        self.discount = 0.8
        self.pre_s = 'Init'
        self.Q.setdefault('Init', {'tap': 0, 'do_nothing': 0})
        self.Q.setdefault('Dead', {'tap': -1000, 'do_nothing': -1000})
        self.pre_a = 'do_nothing'
        self.history = []
        self.epsilon = -1
        self.epsilon_end = 0.0
        self.epsilon_decay = 1e-5
        self.episode = 0

        if os.path.isfile('dict_Q'):
            self.Q = pickle.load(open('dict_Q'))

        def do_at_exit():
            pickle.dump(self.Q, open('dict_Q', 'wb'))
            print 'write to dict_Q'

        atexit.register(do_at_exit)

    # this method is auto called every 0.05s by the pyglet
    def run(self):
        if self.game.state == 'PLAY':
            self.tapped = False
            # call plan() to execute your plan
            self.plan(self.get_state())
        else:
            state = self.get_state()
            bird_state = list(state['bird'])
            bird_state[2] = 'dead'
            state['bird'] = bird_state
            # do NOT allow tap
            self.tapped = True
            self.plan(state)
            # restart game
            print 'score:', self.game.record.get(), 'best: ', self.game.record.best_score
            self.game.restart()
            self.game.play()

    # get the state that robot needed
    def get_state(self):
        state = {}
        # bird's position and status(dead or alive)
        state['bird'] = (int(round(self.game.bird.x)), \
                         int(round(self.game.bird.y)), 'alive')
        state['pipes'] = []
        # pipes' position
        for i in range(1, len(self.game.pipes), 2):
            p = self.game.pipes[i]
            if p.x < Game.WINDOW_WIDTH:
                # this pair of pipes shows on screen
                x = int(round(p.x))
                y = int(round(p.y))
                state['pipes'].append((x, y))
                state['pipes'].append((x, y - Game.PIPE_HEIGHT_INTERVAL))
        return state

    # simulate the click action, bird will fly higher when tapped
    # It can be called only once every time slice(every execution cycle of plan())
    def tap(self):
        if not self.tapped:
            self.game.bird.jump()
            self.tapped = True

    # That's where the robot actually works
    # NOTE Put your code here
    def act(self, state):
        self.history.append((self.pre_s, self.pre_a, state))
        if random.random() <= self.epsilon and self.epsilon >= self.epsilon_end:
            act = random.choice(['tap', 'do_nothing'])
            if act == 'tap':
                self.tap()
                self.pre_a = 'tap'
            else:
                self.pre_a = 'do_nothing'
        else:
            if self.Q[state]['tap'] > self.Q[state]['do_nothing']:
                self.tap()
                self.pre_a = 'tap'
            else:
                self.pre_a = 'do_nothing'

        self.pre_s = state

    def update_Q_table(self):
        self.episode += 1
        history = list(reversed(self.history))
        t = 1
        high_death = False
        if history[1][2][2] <= -5:
            high_death = True

        for pre_s, pre_a, state in history:
            if t == 1:
                reward = -1000
            elif high_death and pre_a == 'tap':
                reward = -1000
                high_death = False
            else:
                reward = 1
            self.Q[pre_s][pre_a] = (1 - self.alpha) * self.Q[pre_s][pre_a] + \
                                   self.alpha * (reward + self.discount *
                                                 max(self.Q[state]['tap'], self.Q[state]['do_nothing']))
            t += 1
        self.history = []
        self.pre_s = 'Init'
        self.pre_a = 'do_nothing'
        self.epsilon -= self.epsilon_decay
        print 'Q-Table updated after ', self.episode, ' times of training.'
        pickle.dump(self.Q, open('dict_Q', 'wb'))
        print 'write to dict_Q'

    def plan(self, state):
        if state['bird'][2] == 'dead':
            self.history.append((self.pre_s, self.pre_a, 'Dead'))
            self.update_Q_table()
        else:
            bird_x = state['bird'][0]
            bird_y = state['bird'][1]
            Low_pipe_x = 9999
            Low_pipe_y = 9999
            High_pipe_y = 9999

            for i in range(1, len(state['pipes']), 2):
                if bird_x <= state['pipes'][i][0] + self.game.PIPE_WIDTH:
                    Low_pipe_x = state['pipes'][i][0]
                    Low_pipe_y = state['pipes'][i][1]
                    High_pipe_y = state['pipes'][i - 1][1]
                    break

            dis_x = Low_pipe_x - bird_x
            dis_y_Low = Low_pipe_y - bird_y
            dis_y_High = High_pipe_y - bird_y

            # punishment = Low_pipe_y + self.game.PIPE_HEIGHT_INTERVAL/2 - bird_y

            dis_x /= 10
            dis_y_Low /= 20
            dis_y_High /= 20


            cur_state = (dis_x, dis_y_Low, dis_y_High)

            self.Q.setdefault(cur_state, {'tap': 0, 'do_nothing': 0})
            if cur_state != self.pre_s:
                self.act(cur_state)


if __name__ == '__main__':
    show_window = True
    enable_sound = False
    game = Game()
    game.set_sound(enable_sound)
    bot = Bot(game)


    def update(dt):
        game.update(dt)
        bot.run()


    pyglet.clock.schedule_interval(update, Game.TIME_INTERVAL)

    if show_window:
        window = pyglet.window.Window(Game.WINDOW_WIDTH, Game.WINDOW_HEIGHT, vsync=False)


        @window.event
        def on_draw():
            window.clear()
            game.draw()


        pyglet.app.run()
    else:
        pyglet.app.run()
