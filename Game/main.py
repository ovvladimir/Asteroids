import random
import math
import pyglet
from pyglet.window import key

import distance_module
# from numba import njit

WIDTH, HEIGHT = 960, 720

game_window = pyglet.window.Window(WIDTH, HEIGHT, caption='Asteroids')
game_window.set_location(5, 30)
game_window.set_mouse_visible(visible=False)
counter = pyglet.window.FPSDisplay(window=game_window)

pyglet.resource.path = ["../res"]
pyglet.resource.reindex()

icon = pyglet.resource.image("ship.png")
game_window.set_icon(icon)

keys = dict(Left=False, Right=False, Up=False, Down=False, Fire=False)
paused = [False, True]
game_run = [True]
score = [0]
asteroid_list = []
bullet_list = []
player_icons = []
game_objects = []
background = []
score_label_color = [(255, 100, 100, 255), (255, 100, 100, 0)]
INITIAL_NUMBER_OF_ASTEROIDS = 5
NUMBER_OF_NEW_ASTEROIDS = 3
NUMBER_OF_LIVES = 5

main_batch = pyglet.graphics.Batch()
group_back = pyglet.graphics.OrderedGroup(0)
group_middle = pyglet.graphics.OrderedGroup(1)
group_front = pyglet.graphics.OrderedGroup(2)

player_image = pyglet.resource.image("ship2.png")
bullet_image = pyglet.resource.image("laser.png")
engine_image = pyglet.resource.image("smoke.png")
asteroid_image = pyglet.resource.image("asteroid.png")
bg_image = pyglet.resource.image("star_field.jpg")
bg_image.width, bg_image.height = WIDTH + 2, HEIGHT + 2
for b in range(2):
    background.append(pyglet.sprite.Sprite(
        img=bg_image, x=0 if b == 0 else -WIDTH, y=0, batch=main_batch, group=group_back))
level_label = pyglet.text.Label(
    text='Asteroids', font_name='Arial', bold=True, color=(250, 250, 250, 150),
    font_size=26, x=WIDTH // 2, y=HEIGHT,
    anchor_x='center', anchor_y='top', batch=main_batch, group=group_middle)
score_label = pyglet.text.Label(
    text='Score: 0', font_name='Arial', font_size=16, x=5, y=HEIGHT - 5,
    anchor_x='left', anchor_y='top', batch=main_batch, group=group_middle)
asteroid_label = pyglet.text.Label(
    text='Asteroids: 3', font_name='Arial', font_size=16,
    x=5, y=score_label.y - score_label.font_size * 1.5,
    anchor_x='left', anchor_y='top', batch=main_batch, group=group_middle)
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


class Sprite(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super(Sprite, self).__init__(*args, **kwargs)
        self.velocity_x, self.velocity_y = 0.0, 0.0

    def update_sprite(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

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


class Player(Sprite):
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
        self.ship_radius = player_image.width // 2
        self.collide_size = (player_image.width + player_image.height) // 4

        self.engine_sprite = pyglet.sprite.Sprite(img=engine_image, *args, **kwargs)
        self.engine_sprite.visible = False

        self.opacity = 0  # прозрачность

    def update_sprite(self, dt):
        super(Player, self).update_sprite(dt)
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
        bullet_x = self.x + math.cos(angle_radians) * self.ship_radius
        bullet_y = self.y + math.sin(angle_radians) * self.ship_radius
        new_bullet = Bullet(bullet_x, bullet_y, batch=self.batch, group=group_front)
        new_bullet.rotation = self.rotation
        bullet_vx = math.cos(math.radians(new_bullet.rotation)) * self.bullet_speed
        bullet_vy = -math.sin(math.radians(new_bullet.rotation)) * self.bullet_speed
        new_bullet.velocity_x = bullet_vx
        new_bullet.velocity_y = bullet_vy
        game_objects.append(new_bullet)
        bullet_list.append(new_bullet)
        laser.play()


class Bullet(Sprite):
    def __init__(self, *args, **kwargs):
        super(Bullet, self).__init__(bullet_image, *args, **kwargs)
        # self.scale = 0.7
        self.collide_size = bullet_image.height * 0.5

    def update_sprite(self, dt):
        super(Bullet, self).update_sprite(dt)

        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.delete()  # удаление из видеопамяти
            bullet_list.remove(self)
            game_objects.remove(self)


class Asteroid(Sprite):
    def __init__(self, *args, **kwargs):
        super(Asteroid, self).__init__(asteroid_image, *args, **kwargs)
        self.rotate_speed = random.randint(-50, 50)

    def handle_collision_with(self, other_object):
        if isinstance(other_object, Bullet):
            score[0] += 1
            score_label.text = f"Score: {score[0]}"
            sound.play()
            if self.scale > 0.3:
                for _ in range(NUMBER_OF_NEW_ASTEROIDS):
                    new_asteroid = Asteroid(x=self.x, y=self.y, batch=self.batch, group=self.group)
                    new_asteroid.velocity_x = random.randint(-120, 120) + self.velocity_x
                    new_asteroid.velocity_y = random.randint(-120, 120) + self.velocity_y
                    new_asteroid.scale = self.scale * 0.5
                    new_asteroid.collide_size = self.image.width * new_asteroid.scale * 0.5
                    game_objects.append(new_asteroid)
                    asteroid_list.append(new_asteroid)
            other_object.delete()
            bullet_list.remove(other_object)
            game_objects.remove(other_object)
            self.delete()
            asteroid_list.remove(self)
            game_objects.remove(self)

    def update_sprite(self, dt):
        super(Asteroid, self).update_sprite(dt)
        self.rotation = (self.rotation + self.rotate_speed * dt) % 360


def init_asteroids(batch=None, group=None):
    for _ in range(INITIAL_NUMBER_OF_ASTEROIDS):
        asteroid_x, asteroid_y = random.randrange(WIDTH), random.randrange(HEIGHT)
        while distance_module.distancef(asteroid_x, asteroid_y, *player_ship.position) < 150:
            asteroid_x = random.randrange(WIDTH)
            asteroid_y = random.randrange(HEIGHT)
        new_asteroid = Asteroid(x=asteroid_x, y=asteroid_y, batch=batch, group=group)
        new_asteroid.rotation = random.randrange(360)
        new_asteroid.velocity_x = random.randint(-50, 50)
        new_asteroid.velocity_y = random.randint(-50, 50)
        new_asteroid.collide_size = asteroid_image.width * 0.5
        game_objects.append(new_asteroid)
        asteroid_list.append(new_asteroid)


'''
@njit('float64(float64, float64, float64, float64)')
def distance(x1, y1, x2, y2):
    """возвращает расстояние между двумя точками"""
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
'''


def update(dt):

    for bg in background:
        bg.x += 10 * dt
        if bg.x >= WIDTH:
            bg.x = -WIDTH

    for index, obj_1 in enumerate(game_objects):
        for obj_2 in game_objects[index + 1:]:
            if not (isinstance(obj_1, Player) and isinstance(obj_2, Bullet)):
                """проверка столкновений"""
                collision_distance = obj_1.collide_size + obj_2.collide_size
                actual_distance = distance_module.distancef(*obj_1.position, *obj_2.position)
                if actual_distance <= collision_distance:
                    if isinstance(obj_1, Player) and isinstance(obj_2, Asteroid):
                        obj_1.opacity = 0
                        obj_2.delete()
                        asteroid_list.remove(obj_2)
                        game_objects.remove(obj_2)
                        icn = player_icons.pop()
                        icn.delete()
                        sound.play()
                    else:
                        obj_1.handle_collision_with(obj_2)

    asteroid_label.text = f"Asteroids: {len(asteroid_list)}"
    if (len(asteroid_list) <= 0 or len(player_icons) <= 0) and game_run[0]:
        game_run[0] = False
        pyglet.clock.unschedule(update)
        pyglet.clock.schedule_interval_soft(text, 1)

    [obj.update_sprite(dt) for obj in game_objects if not paused[0]]


@game_window.event
def on_draw():
    game_window.clear()

    if game_run[0]:
        main_batch.draw()
        counter.draw()
        if paused[0]:
            game_over_label.text = 'PAUSE'
            game_over_label.draw()
    else:
        if score[0] == INITIAL_NUMBER_OF_ASTEROIDS * 13:
            game_over_label.text = 'YOU ROCK!'
        else:
            game_over_label.text = 'GAME OVER'
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
    if symbol == key.P and game_run[0]:
        paused.reverse()
    elif symbol == key.ENTER and not game_run[0]:
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


def text(_):
    score_label_color.reverse()
    score_label.color = score_label_color[0]


def init():
    pyglet.clock.unschedule(text)
    pyglet.clock.schedule_interval(update, 1 / 60.0)
    score[0] = 0
    score_label.text = f"Score: {score[0]}"
    score_label.color = (255, 255, 255, 255)
    for al in asteroid_list:
        al.delete()
    for bl in bullet_list:
        bl.delete()
    for il in player_icons:
        il.delete()
    asteroid_list.clear()
    bullet_list.clear()
    player_icons.clear()
    game_objects.clear()
    game_objects.append(player_ship)
    player_ship.opacity = 0
    player_ship.ship_speed = 0
    player_ship.rotation = 0
    player_ship.position = WIDTH // 2, HEIGHT // 2
    for i in range(NUMBER_OF_LIVES):
        player_icons.append(pyglet.sprite.Sprite(
            player_image, x=WIDTH - player_image.width // 4 - i * 30,
            y=HEIGHT - player_image.height // 4, batch=main_batch, group=group_middle))
        player_icons[i].scale = 0.33
    init_asteroids(main_batch, group_front)
    game_run[0] = True


if __name__ == '__main__':
    player_ship = Player(batch=main_batch, group=group_front)
    init()
    pyglet.app.run()
