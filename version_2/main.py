import pyglet
import random
import math
from pyglet.window import key

import sys
if sys.version_info.minor == 8:  # для версии python 3.8
    import pyglet_ffmpeg2

WIDTH, HEIGHT = 960, 720

game_window = pyglet.window.Window(WIDTH, HEIGHT, caption='Asteroids')
game_window.set_location(5, 30)
game_window.set_mouse_visible(visible=False)
counter = pyglet.window.FPSDisplay(window=game_window)

pyglet.resource.path = ["../res"]
pyglet.resource.reindex()

icon = pyglet.resource.image("ship.png")
game_window.set_icon(icon)

backgraund = [0, -WIDTH]
keys = dict(Left=False, Right=False, Up=False, Down=False, Fire=False)
paused = [False, True]
game_run = [True]
score = [0]
asteroid_list = []
bullet_list = []
player_icons = []
game_objects = []
INITIAL_NUMBER_OF_ASTEROIDS = 3
NUMBER_OF_LIVES = 5

main_batch = pyglet.graphics.Batch()  # рисуем (draw) все изображения сразу
player_image = pyglet.resource.image("ship2.png")
bullet_image = pyglet.resource.image("laser.png")
engine_image = pyglet.resource.image("smoke.png")
asteroid_image = pyglet.resource.image("asteroid.png")
star_field_image = pyglet.resource.image("starfield.jpg")
level_label = pyglet.text.Label(
    text='Asteroids', font_name='Arial', bold=True, color=(250, 250, 250, 150),
    font_size=26, x=WIDTH // 2, y=HEIGHT,
    anchor_x='center', anchor_y='top', batch=main_batch)
score_label = pyglet.text.Label(
    text='Points: 0', font_name='Arial', font_size=16,
    x=5, y=HEIGHT - 5, anchor_x='left', anchor_y='top', batch=main_batch)
asteroid_label = pyglet.text.Label(
    text='Asteroids: 3', font_name='Arial', font_size=16,
    x=5, y=score_label.y - score_label.font_size * 1.5,
    anchor_x='left', anchor_y='top', batch=main_batch)
game_over_label = pyglet.text.Label(
    '', font_name='Arial', font_size=36, color=(50, 50, 255, 255),
    x=WIDTH // 2, y=HEIGHT // 2,
    anchor_x='center', anchor_y='center')
new_game_label = pyglet.text.Label(
    '', font_name='Arial', font_size=26, color=(250, 250, 250, 150),
    x=WIDTH // 2, y=game_over_label.y - game_over_label.font_size * 2,
    anchor_x='center', anchor_y='center')
laser = pyglet.resource.media('laser.wav', streaming=False)
sound = pyglet.resource.media('explosion.wav', streaming=False)

player_image.anchor_x, player_image.anchor_y = player_image.width // 2, player_image.height // 2
asteroid_image.anchor_x, asteroid_image.anchor_y = asteroid_image.width // 2, asteroid_image.height // 2
bullet_image.anchor_x, bullet_image.anchor_y = bullet_image.width // 2, bullet_image.height // 2
engine_image.anchor_x, engine_image.anchor_y = engine_image.width * 1.5, engine_image.height * 0.5


class Object(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.velocity_x, self.velocity_y = 0.0, 0.0
        self.dead = False

    def update(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.check_bounds()

    def check_bounds(self):
        min_x = -self.image.width // 2
        min_y = -self.image.height // 2
        max_x = WIDTH - min_x
        max_y = HEIGHT - min_y
        if self.x < min_x:
            self.x = max_x
        elif self.x > max_x:
            self.x = min_x
        elif self.y < min_y:
            self.y = max_y
        elif self.y > max_y:
            self.y = min_y

    def collides_with(self, other_object):
        collision_distance = self.image.width // 2 * self.scale \
            + other_object.image.width // 2 * other_object.scale
        actual_distance = distance(self.position, other_object.position)
        return actual_distance <= collision_distance

    def handle_collision_with(self, other_object):
        if other_object.__class__ is not self.__class__:
            self.dead = True
            if self in asteroid_list:
                score[0] += 1
                score_label.text = f"Points: {score[0]}"
                sound.play()


class Player(Object):
    def __init__(self, *args, **kwargs):
        super(Player, self).__init__(img=player_image, *args, **kwargs)
        self.ship_thrust = 0
        self.ship_max_speed = 400
        self.ship_speed = 0
        self.ship_drag = 5
        self.rotate_speed = 200
        self.bullet_speed = 800
        self.rotation = 0
        self.position = WIDTH // 2, HEIGHT // 2

        self.engine_sprite = pyglet.sprite.Sprite(img=engine_image, *args, **kwargs)
        self.engine_sprite.visible = False

        self.opacity = 0  # прозрачность

    def update(self, dt):
        super(Player, self).update(dt)
        self.ship_speed += self.ship_thrust
        if self.ship_speed > 0:
            self.ship_speed -= self.ship_drag
            if self.ship_speed < 0:
                self.ship_speed = 0
        if self.ship_speed < 0:
            self.ship_speed += self.ship_drag
            if self.ship_speed > 0:
                self.ship_speed = 0
        if self.ship_speed > self.ship_max_speed:
            self.ship_speed = self.ship_max_speed
        if self.ship_speed < -self.ship_max_speed:
            self.ship_speed = -self.ship_max_speed
        angle_radians = -math.radians(self.rotation)
        force_x = math.cos(angle_radians) * self.ship_speed * dt
        force_y = math.sin(angle_radians) * self.ship_speed * dt
        self.x += force_x
        self.y += force_y

        self.engine_sprite.rotation = self.rotation
        self.engine_sprite.x = self.x
        self.engine_sprite.y = self.y

        if self.opacity == 255:
            if keys['Fire'] and len(bullet_list) == 0:
                self.fire()
            if keys['Left']:
                self.rotation -= self.rotate_speed * dt
            if keys['Right']:
                self.rotation += self.rotate_speed * dt
            if keys['Up']:
                self.ship_thrust = 20
                self.engine_sprite.visible = True
            elif keys['Down']:
                self.ship_thrust = -20
                self.engine_sprite.visible = True
            else:
                self.ship_thrust = 0
                self.engine_sprite.visible = False
        else:
            self.engine_sprite.visible = False
            self.ship_speed = 0
            self.rotation = 0
            self.position = WIDTH // 2, HEIGHT // 2

            self.opacity += 2
            if self.opacity >= 255:
                self.opacity = 255

    def fire(self):
        angle_radians = -math.radians(self.rotation)
        ship_radius = self.image.width // 2
        bullet_x = self.x + math.cos(angle_radians) * ship_radius
        bullet_y = self.y + math.sin(angle_radians) * ship_radius
        new_bullet = Bullet(bullet_x, bullet_y, batch=self.batch)
        new_bullet.scale = 0.7
        new_bullet.rotation = self.rotation
        bullet_vx = math.cos(math.radians(new_bullet.rotation)) * self.bullet_speed
        bullet_vy = -math.sin(math.radians(new_bullet.rotation)) * self.bullet_speed
        new_bullet.velocity_x = bullet_vx
        new_bullet.velocity_y = bullet_vy
        game_objects.append(new_bullet)
        bullet_list.append(new_bullet)
        laser.play()


class Bullet(Object):
    def __init__(self, *args, **kwargs):
        super(Bullet, self).__init__(bullet_image, *args, **kwargs)

    def update(self, dt):
        super(Bullet, self).update(dt)

        if self.x < 0:
            self.dead = True
        elif self.x > WIDTH:
            self.dead = True
        elif self.y < 0:
            self.dead = True
        elif self.y > HEIGHT:
            self.dead = True


class Asteroid(Object):
    def __init__(self, *args, **kwargs):
        super(Asteroid, self).__init__(asteroid_image, *args, **kwargs)
        self.rotate_speed = random.randint(-50, 50)

    def handle_collision_with(self, other_object):
        super(Asteroid, self).handle_collision_with(other_object)
        if self.dead and self.scale > 0.3:
            num_asteroids = 3
            for _ in range(num_asteroids):
                new_asteroid = Asteroid(x=self.x, y=self.y, batch=self.batch)
                new_asteroid.velocity_x = random.randint(-120, 120) + self.velocity_x
                new_asteroid.velocity_y = random.randint(-120, 120) + self.velocity_y
                new_asteroid.scale = self.scale * 0.5
                game_objects.append(new_asteroid)
                asteroid_list.append(new_asteroid)

    def update(self, dt):
        super(Asteroid, self).update(dt)
        self.rotation = (self.rotation + self.rotate_speed * dt) % 360


def asteroid(num_asteroids, player_position, batch=None):
    asteroids = []
    for _ in range(num_asteroids):
        asteroid_x, asteroid_y = player_position
        while distance((asteroid_x, asteroid_y), player_position) < 100:
            asteroid_x = random.randint(0, WIDTH)
            asteroid_y = random.randint(0, HEIGHT)
        new_asteroid = Asteroid(x=asteroid_x, y=asteroid_y, batch=batch)
        new_asteroid.rotation = random.randint(0, 360)
        new_asteroid.velocity_x = random.randint(-40, 40)
        new_asteroid.velocity_y = random.randint(-40, 40)
        asteroids.append(new_asteroid)
    return asteroids


def distance(point_1=(0, 0), point_2=(0, 0)):
    """Возвращает расстояние между двумя точками"""
    return math.sqrt((point_1[0] - point_2[0]) ** 2 + (point_1[1] - point_2[1]) ** 2)


def update(dt):
    [obj.update(dt) for obj in game_objects if paused[0] is False and game_run[0] is True]

    # смещение фона
    backgraund[0] += 0.1
    backgraund[1] += 0.1
    if backgraund[0] >= WIDTH:
        backgraund[0] = 0
    if backgraund[1] >= 0:
        backgraund[1] = -WIDTH

    for index, obj_1 in enumerate(game_objects):
        for obj_2 in game_objects[index + 1:]:
            if not obj_1.dead and not obj_2.dead:
                if not (isinstance(obj_1, Player) and isinstance(obj_2, Bullet)):
                    if obj_1.collides_with(obj_2):
                        if isinstance(obj_1, Player) and isinstance(obj_2, Asteroid):
                            obj_1.opacity = 0
                            obj_2.dead = True
                            player_icons[-1].delete()
                            player_icons.pop()
                            sound.play()
                        else:
                            obj_1.handle_collision_with(obj_2)
                            obj_2.handle_collision_with(obj_1)

    for obj in game_objects:
        if obj.dead:
            if obj is not player_ship:
                obj.delete()
                game_objects.remove(obj)
                if obj in bullet_list:
                    bullet_list.remove(obj)
                if isinstance(obj, Asteroid):
                    asteroid_list.remove(obj)

    asteroid_label.text = f"Asteroids: {len(asteroid_list)}"
    if len(asteroid_list) <= 0 or len(player_icons) <= 0:
        game_run[0] = False


@game_window.event
def on_draw():
    game_window.clear()

    for bg in backgraund:
        star_field_image.blit(bg, 0, width=WIDTH, height=HEIGHT)

    if game_run[0] is True:
        main_batch.draw()
        counter.draw()
        if paused[0] is True:
            game_over_label.text = "PAUSE"
            game_over_label.draw()
    else:
        if score[0] > 38:
            game_over_label.text = "YOU ROCK!"
        elif len(asteroid_list) <= 0 and score[0] / (5 - len(player_icons)) > 1 and len(player_icons) > 0:
            game_over_label.text = "VICTORY!"
        elif len(player_icons) <= 0 or len(asteroid_list) <= 0:
            game_over_label.text = "GAME OVER"
        new_game_label.text = 'press Enter for a new game'
        new_game_label.draw()
        game_over_label.draw()
        asteroid_label.draw()
        score_label.draw()
        level_label.draw()
        for i in player_icons:
            i.draw()


@game_window.event
def on_key_press(symbol, modifiers):
    if symbol == key.P and game_run[0] is True:
        paused.reverse()
    elif symbol == key.ENTER and game_run[0] is False:
        init()
    elif modifiers & key.MOD_CTRL:
        pass

    if symbol == key.UP:
        keys['Up'] = True
    if symbol == key.DOWN:
        keys['Down'] = True
    if symbol == key.LEFT:
        keys['Left'] = True
    if symbol == key.RIGHT:
        keys['Right'] = True
    if symbol == key.SPACE:
        keys['Fire'] = True


@game_window.event
def on_key_release(symbol, modifiers):
    if symbol == key.UP:
        keys['Up'] = False
    if symbol == key.DOWN:
        keys['Down'] = False
    if symbol == key.LEFT:
        keys['Left'] = False
    if symbol == key.RIGHT:
        keys['Right'] = False
    if symbol == key.SPACE:
        keys['Fire'] = False
    if modifiers & key.MOD_CTRL:
        pass


def init():
    score[0] = 0
    score_label.text = f"Points: {score[0]}"
    for al in asteroid_list:
        al.delete()
    for pi in player_icons:
        pi.delete()
    for bl in bullet_list:
        bl.delete()
    asteroid_list.clear()
    bullet_list.clear()
    player_icons.clear()
    game_objects.clear()
    for i in range(NUMBER_OF_LIVES):
        player_icons.append(pyglet.sprite.Sprite(
            player_image, x=WIDTH - player_image.width // 4 - i * 30,
            y=HEIGHT - player_image.height // 4, batch=main_batch))
        player_icons[i].scale = 0.33
    asteroid_list.extend(asteroid(INITIAL_NUMBER_OF_ASTEROIDS, player_ship.position, main_batch))
    game_objects.extend([player_ship] + asteroid_list)
    player_ship.opacity = 0
    player_ship.ship_speed = 0
    player_ship.rotation = 0
    player_ship.position = WIDTH // 2, HEIGHT // 2
    game_run[0] = True


if __name__ == '__main__':
    player_ship = Player(x=WIDTH // 2, y=HEIGHT // 2, batch=main_batch)
    init()

    pyglet.clock.schedule_interval(update, 1 / 60.0)
    pyglet.app.run()
