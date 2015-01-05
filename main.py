#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bombicka what? Collect bombicka, use bombicka.
"""

# import cProfile, pstats

import random
import time
from math import trunc

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import NumericProperty, BooleanProperty, \
    ReferenceListProperty, ObjectProperty, StringProperty
from kivy.vector import Vector
from kivy.animation import Animation
from kivy.metrics import dp


__author__  = 'Martin Veselovský'
__email__   = 'martin.veselovskyy@gmail.com'
__version__ = '1.1.0'

bg_color = 0.407, 0.517, 0.498


class Player(Widget):
    """
    Player object definition and interaction
    """

    # shooting
    score_res = NumericProperty(0)
    score_kill = NumericProperty(0)
    killed = BooleanProperty(0)
    death_time = 4
    fire_time = 3.5
    ai_accuracy = 150
    ai_frequency = 3
    ai_fire_time = 0

    # movement
    gpos = []  # goal position
    speed_const = dp(2)  # common speed
    speed = speed_const  # actual speed - used for opposite direction
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    text = StringProperty()

    def life(self, dt):
        """ Back to life """
        self.fire.hide()
        self.killed = False
        self.text = "I am alive :)"

    def death(self):
        """ Disable movement and stay dead for a while """
        self.pos = self.center
        self.gpos = self.center
        self.killed = True
        self.fire.show(self.pos)
        self.text = "I am dead :("
        Clock.schedule_once(self.life, self.death_time)

    def move(self):
        """ Move player if he's not dead """
        if self.killed:
            return

        dx = trunc(self.gpos[0] - self.center_x)
        dy = trunc(self.gpos[1] - self.center_y)

        # set velocity in x direction
        if abs(dx) > self.speed_const:
            self.velocity_x = self.speed if dx > 0 else -self.speed
        else:
            self.velocity_x = 0
            self.center_x = self.gpos[0]

        # set velocity in y direction
        if abs(dy) > self.speed_const:
            self.velocity_y = self.speed if dy > 0 else -self.speed
        else:
            self.velocity_y = 0
            self.center_y = self.gpos[1]

        self.pos = Vector(*self.velocity) + self.pos


class Fire(Widget):
    """
    Player on fire, player is currently dead
    """

    init_size1 = dp(60), dp(60)
    init_size2 = dp(70), dp(70)

    transparent = NumericProperty(0)
    anim = ObjectProperty(None)

    def show(self, pos):
        """ Show pulsing fire at player's position. Player is on fire. """
        self.pos = pos[0] - self.size[0] / 10, pos[1] - self.size[1] / 10
        self.transparent = 1
        self.anim = Animation(size=self.init_size2, duration=0.1) + Animation(size=self.init_size1,
                                                                              duration=0.1)
        self.anim.repeat = True
        self.anim.start(self)

    def hide(self):
        """ Hide pulsing fire """
        self.transparent = 0
        self.anim.cancel(self)


class Resource(Widget):
    """
    One resource at time in game, ready to collect by players
    """
    pass


class Explosion(Widget):
    """
    Representation of explosion
    """

    is_now = False
    start = 0.5
    duration = 1.0
    init_size1 = dp(140), dp(140)
    init_size2 = dp(142), dp(142)

    transparent = NumericProperty(0)
    anim = ObjectProperty(None)
    end_time = NumericProperty(0)

    def show(self, pos):
        """ Show pulsing explosion on touch position """
        self.end_time = time.time() + self.duration
        self.transparent = 0.8
        self.is_now = True
        self.center = pos

        self.anim = Animation(size=self.init_size2, duration=0.1) + \
                    Animation(size=self.init_size1, duration=0.1)
        self.anim.repeat = True
        self.anim.start(self)

    def hide(self):
        """ Hide pulsing explosion """
        self.transparent = 0
        self.is_now = False
        self.anim.cancel(self)


class Game(Widget):
    """
    Game controller
    """

    # objects
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    resource = ObjectProperty(None)
    explosion1 = ObjectProperty(None)
    explosion2 = ObjectProperty(None)

    # interaction
    touch = False
    touch_time = 0

    bg_color = bg_color

    def update(self, dt):
        """
        Update all game mechanics - players movements, resource, explosions, fires
        """

        self.player1.move()
        self.player2.move()

        if self.player1.killed and self.player2.killed:
            self.player1.killed = False  # reset

        # disturbing both on collision
        if self.player1.collide_widget(self.player2):
            self.player1.gpos = (random.randint(0, self.width), random.randint(0, self.height))
            self.player2.gpos = (random.randint(0, self.width), random.randint(0, self.height))
            self.player1.text = "vrr.."
            self.player2.text = "vrr.."
        else:
            self.player2.gpos = self.resource.center
            self.player2.text = ""

        # gathering resources
        if self.player1.collide_widget(self.resource):
            self.player1.score_res += 1
            self.player2.killed = False
            self.resource.center = (random.randint(0, self.width), random.randint(0, self.height))

        if self.player2.collide_widget(self.resource):
            self.player2.score_res += 1
            self.player1.killed = False
            self.resource.center = (random.randint(0, self.width), random.randint(0, self.height))
            self.player2.ai_fire_time = time.time()

        # making explosions
        if self.touch and self.player1.score_res > 0 and time.time() > self.touch_time + self.explosion1.start:
            # explosion and player1 run away
            self.explosion1.show(self.player1.gpos)
            self.player1.score_res -= 1
            self.player1.speed = -self.player1.speed_const
            self.player1.text = "Run away !"

        # making AI explosions
        if self.player2.score_res > 0 and self.player2.ai_fire_time + self.player2.ai_frequency < time.time():
            self.player2.score_res -= 1
            self.player2.ai_fire_time = time.time()
            Clock.schedule_once(self.ai_explosion, self.player2.ai_frequency)

        # destroy player2
        if self.explosion1.is_now:
            if self.player2.collide_widget(self.explosion1) and not self.player2.killed:
                self.player2.death()
                self.player1.score_kill += 1

            # end of explosion
            if time.time() > self.explosion1.end_time:
                self.explosion1.hide()
                self.player1.speed = self.player1.speed_const
                self.player1.text = ""

        # destroy player1
        if self.explosion2.is_now:
            if self.player1.collide_widget(self.explosion2) and not self.player1.killed:
                self.player1.death()
                self.player2.score_kill += 1

            # end of explosion
            if time.time() > self.explosion2.end_time:
                self.explosion2.hide()
                self.player2.speed = self.player2.speed_const
                self.player2.text = ""

    def on_touch_down(self, touch):
        """ Set goal position from touch position if player is not dead """
        if self.player1.killed:
            return
        self.touch = True
        self.touch_time = time.time()
        self.player1.gpos = (touch.x, touch.y)
        self.player1.text = ""

    def on_touch_up(self, touch):
        """ end of touch interaction """
        self.touch = False

    def ai_explosion(self, dt):
        """
        if AI player has already a resource, then plan random explosion near player1
        """
        if not self.player2.killed:
            x = trunc(self.player1.center_x)
            y = trunc(self.player1.center_y)

            self.player2.text = "Run away !"
            self.explosion2.show(
                (random.randint(x - self.player2.ai_accuracy, x + self.player2.ai_accuracy),
                 random.randint(y - self.player2.ai_accuracy, y + self.player2.ai_accuracy))
            )
            self.player2.speed = -self.player2.speed_const
        else:
            Clock.schedule_once(self.ai_explosion, self.player2.ai_frequency)


class BombickaApp(App):
    """
    Application class, create game and schedule interval of game updating
    """

    def build(self):
        """ Create the application and schedule update of game """
        game = Game()
        Clock.schedule_interval(game.update, 1.0 / 70.0)
        return game

        # def on_start(self):
        # self.profile = cProfile.Profile()
        #     self.profile.enable()
        #
        # def on_stop(self):
        #     self.profile.disable()
        #
        #     f = open('x.prof', 'a')
        #     sortby = 'cumulative'
        #     pstats.Stats(self.profile, stream=f).strip_dirs().sort_stats(sortby).print_stats()
        #     f.close()


if __name__ == '__main__':
    BombickaApp().run()
