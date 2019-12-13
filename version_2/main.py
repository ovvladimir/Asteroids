# https://pyglet.readthedocs.io/en/stable/
import pyglet
import random
import math
from pyglet.window import key

game_window = pyglet.window.Window(960, 720, caption='Asteroids')
game_window.set_location(5, 30)
game_window.set_mouse_visible(visible=False)

pyglet.resource.path = ['../res']
pyglet.resource.reindex()

icon = pyglet.resource.image('ship.png')
game_window.set_icon(icon)

backgraund_x1 = [0]
backgraund_x2 = [-game_window.width]
keys = dict(Left=False, Right=False, Up=False, Down=False, Fire=False)
game_run = [True]
paused = [False, True]
score = [0]
num_icons = [6]
asteroid_list = []
bullet_list = []

main_batch = pyglet.graphics.Batch()  # рисуем (draw) все изображения сразу
player_image = pyglet.resource.image("ship2.png")
bullet_image = pyglet.resource.image("laser.png")
engine_image = pyglet.resource.image("smoke.png")
asteroid_image = pyglet.resource.image("asteroid.png")
star_field_image = pyglet.resource.image('starfield.jpg')
level_label = pyglet.text.Label(text="Asteroids", font_name='Times New Roman', bold=True,
                                font_size=28, x=game_window.width // 2, y=game_window.height - 32,
                                anchor_x='center', batch=main_batch)
score_label = pyglet.text.Label(text=f"Points: {score[0]}", font_name='Times New Roman',
                                font_size=16, x=10, y=game_window.height - 25, batch=main_batch)
asteroid_label = pyglet.text.Label(text=f"Asteroids: {len(asteroid_list)}", font_name='Times New Roman',
                                   font_size=16, x=10, y=game_window.height - 55, batch=main_batch)
game_over_label = pyglet.text.Label('',
                                    font_name='Arial', font_size=36, color=(50, 50, 255, 255),
                                    x=game_window.width // 2, y=game_window.height // 2,
                                    anchor_x='center', anchor_y='center')
laser = pyglet.resource.media('laser.wav', streaming=False)
sound = pyglet.resource.media('explosion.wav', streaming=False)
"""player_ship = pyglet.sprite.Sprite(x=game_window.width/2, y=game_window.height/2, batch=main_batch)"""
counter = pyglet.window.FPSDisplay(window=game_window)


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
        min_x = -self.image.width / 2.
        min_y = -self.image.height / 2.
        max_x = game_window.width - min_x
        max_y = game_window.height - min_y
        if self.x < min_x:
            self.x = max_x
        elif self.x > max_x:
            self.x = min_x
        elif self.y < min_y:
            self.y = max_y
        elif self.y > max_y:
            self.y = min_y

    def collides_with(self, other_object):
        collision_distance = self.image.width / 2. * self.scale \
            + other_object.image.width / 2. * other_object.scale
        actual_distance = distance(self.position, other_object.position)
        return actual_distance <= collision_distance

    def handle_collision_with(self, other_object):
        if other_object.__class__ is not self.__class__:
            self.dead = True
            if self in asteroid_list:
                score[0] += 1
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
        self.position = game_window.width / 2., game_window.height / 2.

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

        if self.opacity >= 255:
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
            self.position = game_window.width / 2., game_window.height / 2.

        if self.opacity == 0:
            num_icons[0] -= 1
        self.opacity += 2
        if self.opacity >= 255:
            self.opacity = 255

    def fire(self):
        angle_radians = -math.radians(self.rotation)
        ship_radius = self.image.width / 2
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
    """Пули, выпущенные игроком"""
    def __init__(self, *args, **kwargs):
        super(Bullet, self).__init__(bullet_image, *args, **kwargs)

    def update(self, dt):
        super(Bullet, self).update(dt)

        if self.x < 0:
            self.dead = True
        elif self.x > game_window.width:
            self.dead = True
        elif self.y < 0:
            self.dead = True
        elif self.y > game_window.height:
            self.dead = True


class Asteroid(Object):
    def __init__(self, *args, **kwargs):
        super(Asteroid, self).__init__(asteroid_image, *args, **kwargs)
        self.rotate_speed = random.random() * 100.0 - 50.0

    def handle_collision_with(self, other_object):
        super(Asteroid, self).handle_collision_with(other_object)
        if self.dead and self.scale > 0.3:
            num_asteroids = 3
            for i in range(num_asteroids):
                new_asteroid = Asteroid(x=self.x,  # +i*50*random.choice([-1, 1]),
                                        y=self.y,  # +i*50*random.choice([-1, 1]),
                                        batch=self.batch)
                new_asteroid.rotation = random.randint(50 * i, 360)
                new_asteroid.velocity_x = (random.random() * 40 * random.choice([-1, 1])
                                           + self.velocity_x) * random.choice([1, 3])
                new_asteroid.velocity_y = (random.random() * 40 * random.choice([-1, 1])
                                           + self.velocity_y) * random.choice([1, 3])
                new_asteroid.scale = self.scale * 0.5
                game_objects.append(new_asteroid)
                asteroid_list.append(new_asteroid)

    def update(self, dt):
        super(Asteroid, self).update(dt)
        self.rotation += self.rotate_speed * dt


def center_image(image):
    """Точка привязки изображения по центру"""
    image.anchor_x = image.width / 2.
    image.anchor_y = image.height / 2.


def asteroid(num_asteroids, player_position, batch=None):
    asteroids = []
    for i in range(num_asteroids):
        asteroid_x, asteroid_y = player_position
        while distance((asteroid_x, asteroid_y), player_position) < 100:
            asteroid_x = random.randint(0, game_window.width)
            asteroid_y = random.randint(0, game_window.height)
        new_asteroid = Asteroid(x=asteroid_x, y=asteroid_y,
                                batch=batch)
        new_asteroid.rotation = random.randint(10, 360)
        new_asteroid.velocity_x = random.random() * 40 * random.choice([-1, 1])
        new_asteroid.velocity_y = random.random() * 40 * random.choice([-1, 1])
        asteroids.append(new_asteroid)
    return asteroids


def distance(point_1=(0, 0), point_2=(0, 0)):
    """Возвращает расстояние между двумя точками"""
    return math.sqrt((point_1[0] - point_2[0]) ** 2 + (point_1[1] - point_2[1]) ** 2)


def update(dt):
    [obj.update(dt) for obj in game_objects if paused[0] is False and game_run[0] is True]

    # смещение фона
    backgraund_x1[0] += 0.1
    backgraund_x2[0] += 0.1
    if backgraund_x1[0] >= game_window.width:
        backgraund_x1[0] = 0
    if backgraund_x2[0] >= 0:
        backgraund_x2[0] = -game_window.width

    for i in range(len(game_objects)):
        for j in range(i + 1, len(game_objects)):
            obj_1 = game_objects[i]
            obj_2 = game_objects[j]
            if not obj_1.dead and not obj_2.dead:
                if not (obj_1 is player_ship and obj_2 in bullet_list):
                    if obj_1.collides_with(obj_2):
                        if obj_1 is player_ship and obj_2 in asteroid_list:
                            obj_1.opacity = 0
                            obj_2.dead = True
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
                if obj in asteroid_list:
                    asteroid_list.remove(obj)

    if len(asteroid_list) <= 0 or num_icons[0] <= 0:
        game_run[0] = False


@game_window.event
def on_key_press(symbol, modifiers):
    if symbol == key.P:
        paused.reverse()
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


@game_window.event
def on_draw():
    game_window.clear()

    star_field_image.blit(backgraund_x1[0], 0, width=game_window.width, height=game_window.height)
    star_field_image.blit(backgraund_x2[0], 0, width=game_window.width, height=game_window.height)
    asteroid_label.text = f"Asteroids: {len(asteroid_list)}"
    score_label.text = f"Points: {score[0]}"
    for i in range(num_icons[0]):
        player_image.blit(x=game_window.width - i * 30, y=game_window.height,
                          width=player_image.width // 3, height=player_image.height // 3)
    if game_run[0] is True:
        if paused[0] is False:
            main_batch.draw()
            counter.draw()
        else:
            game_over_label.text = "PAUSE"
            game_over_label.draw()
            asteroid_label.draw()
            score_label.draw()
            level_label.draw()
    else:
        if score[0] > 38:
            game_over_label.text = "YOU ROCK!"
        else:
            game_over_label.text = "GAME OVER"
        game_over_label.draw()
        asteroid_label.draw()
        score_label.draw()
        level_label.draw()


if __name__ == '__main__':
    player_ship = Player(x=game_window.width // 2, y=game_window.height // 2, batch=main_batch)
    asteroid_list = asteroid(3, player_ship.position, main_batch)  # 3 - кол-во астероидов
    game_objects = [player_ship] + asteroid_list

    engine_image.anchor_x = engine_image.width * 1.5
    engine_image.anchor_y = engine_image.height * 0.5
    center_image(player_image)
    center_image(asteroid_image)
    center_image(bullet_image)

    pyglet.clock.schedule_interval(update, 1 / 120.0)
    pyglet.app.run()
