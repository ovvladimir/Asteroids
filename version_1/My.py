import pyglet
import random
import math
from pyglet.window import key

game_window = pyglet.window.Window(960, 720)

pyglet.resource.path = ['../res']
pyglet.resource.reindex()

x1 = 0
x2 = -game_window.width
SCORE = 0
AST = 3
paused = False
game = True
keys = dict(Left=False,  Right=False,  Up=False, Down=False, Fire=False)
block = [True, False]
COLLISION_RESOLUTION = 10
num_icons = 6
num_icon = 0

player_image = pyglet.resource.image("ship2.png")
bullet_image = pyglet.resource.image("laser.png")
engine_image = pyglet.resource.image("smoke.png")
star_field_image = pyglet.resource.image('starfield.jpg')

asteroid_image = pyglet.resource.image("asteroid.png")
main_batch = pyglet.graphics.Batch()  # рисуем (draw) все изображения сразу
level_label = pyglet.text.Label(text="My Game", font_name='Times New Roman',
                                font_size=24, x=game_window.width/2, y=game_window.height-30,
                                anchor_x='center', batch=main_batch)
score_label = pyglet.text.Label(text="Очки: " + str(SCORE), font_name='Times New Roman',
                                font_size=16, x=10, y=game_window.height-25, batch=main_batch)
asteroid_label = pyglet.text.Label(text="Астероиды: " + str(AST), font_name='Times New Roman',
                                   font_size=16, x=10, y=game_window.height-55, batch=main_batch)
game_over_label = pyglet.text.Label('',
                                    font_name='Arial', font_size=36, color=(50, 50, 255, 255),
                                    x=game_window.width/2, y=game_window.height/2,
                                    anchor_x='center', anchor_y='center')
laser = pyglet.resource.media('laser.wav', streaming=False)
sound = pyglet.resource.media('explosion.wav', streaming=False)
"""player_ship = pyglet.sprite.Sprite(x=game_window.width/2, y=game_window.height/2, batch=main_batch)"""


class Object(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.velocity_x, self.velocity_y = 0.0, 0.0
        self.x = self.x
        self.y = self.y

        self.dead = False

        self.collision_radius = self.image.width // COLLISION_RESOLUTION // 2

    def update(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.check_bounds()

    def check_bounds(self):
        global db
        db = 1

        min_x = -self.image.width / 2
        min_y = -self.image.height / 2
        max_x = game_window.width + self.image.width / 2
        max_y = game_window.height + self.image.height / 2
        if self.x < min_x:
            self.x = max_x
        elif self.x > max_x:
            self.x = min_x
        elif self.y < min_y:
            self.y = max_y
        elif self.y > max_y:
            self.y = min_y
        else:
            db = 0

    def collides_with(self, other_object):
        collision_distance = self.image.width / 2 + other_object.image.width / 2
        actual_distance = distance(self.position, other_object.position)
        return actual_distance <= collision_distance

    def handle_collision_with(self, other_object):
        global SCORE
        if other_object.__class__ == self.__class__:
            self.dead = False
        else:
            self.dead = True
            SCORE += 0.5
            sound.play()

    def collision_cells(self):
        radius = self.collision_radius
        cellx = int(self.x / COLLISION_RESOLUTION)
        celly = int(self.y / COLLISION_RESOLUTION)
        for y in range(celly - radius, celly + radius + 1):
            for x in range(cellx - radius, cellx + radius + 1):
                yield x, y


class Player(Object):
    def __init__(self, *args, **kwargs):
        super().__init__(img=player_image, *args, **kwargs)
        self.ship_thrust = 0
        self.ship_max_speed = 400
        self.ship_speed = 0
        self.ship_drag = 5
        self.rotate_speed = 200
        self.bullet_speed = 800
        self.rotation = 0
        self.position = game_window.width / 2, game_window.height / 2

        self.engine_sprite = pyglet.sprite.Sprite(img=engine_image, *args, **kwargs)
        self.engine_sprite.visible = False

        self.fire_timeout = 0
        self.opacity = 0  # прозрачность

        self.hit = False

    def update(self, dt):
        super(Player, self).update(dt)
        global num_icon
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

        self.fire_timeout -= dt
        if self.opacity >= 255:
            if keys['Fire'] and self.fire_timeout <= 0:
                self.fire_timeout = 1.5  # промежуток между пулями
                self.fire()
            elif keys['Left']:
                self.rotation -= self.rotate_speed * dt
            elif keys['Right']:
                self.rotation += self.rotate_speed * dt
            elif keys['Down']:
                self.ship_thrust = -20
                self.engine_sprite.visible = True
            elif keys['Up']:
                self.engine_sprite.visible = True
                self.ship_thrust = 20
            else:
                self.ship_thrust = 0
                self.engine_sprite.visible = False
        else:
            self.engine_sprite.visible = False
            self.ship_speed = 0
            self.rotation = 0
            self.position = game_window.width / 2, game_window.height / 2

        if self.opacity == 0:
            num_icon += 1
        self.opacity += 5
        if self.opacity >= 255:
            self.opacity = 255

    def delete(self):
        super(Player, self).delete()
        self.engine_sprite.delete()

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
        laser.play()


class Bullet(Object):
    """Пули, выпущенные игроком"""
    def __init__(self, *args, **kwargs):
        super().__init__(bullet_image, *args, **kwargs)

    def die(self):
        self.dead = True

    def update(self, dt):
        super(Bullet, self).update(dt)
        if db == 1:
            self.die()


class Asteroid(Object):
    def __init__(self, *args, **kwargs):
        super(Asteroid, self).__init__(asteroid_image, *args, **kwargs)
        self.rotate_speed = random.random() * 100.0 - 50.0
        self.hit = False

    def handle_collision_with(self, other_object):
        super(Asteroid, self).handle_collision_with(other_object)
        if self.dead and self.scale > 0.3:
            num_asteroids = 3
            for i in range(num_asteroids):
                new_asteroid = Asteroid(x=self.x,  # +i*50*random.choice([-1, 1]),
                                        y=self.y,  # +i*50*random.choice([-1, 1]),
                                        batch=self.batch)
                new_asteroid.rotation = random.randint(50*i, 360)
                new_asteroid.velocity_x = (random.random() * 40 * random.choice([-1, 1])
                                           + self.velocity_x) * random.choice([-1, 1])
                new_asteroid.velocity_y = (random.random() * 40 * random.choice([-1, 1])
                                           + self.velocity_y) * random.choice([-1, 1])
                new_asteroid.scale = self.scale * 0.5
                game_objects.append(new_asteroid)

    def update(self, dt):
        super(Asteroid, self).update(dt)
        self.rotation += self.rotate_speed * dt


def center_image(image):
    """Точка привязки изображения по центру"""
    image.anchor_x = image.width / 2
    image.anchor_y = image.height / 2


engine_image.anchor_x = engine_image.width * 1.5
engine_image.anchor_y = engine_image.height / 2
center_image(player_image)
center_image(asteroid_image)
center_image(bullet_image)


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


def game_over():
    global paused, game
    paused = True
    game = False


player_ship = Player(x=game_window.width/2, y=game_window.height/2, batch=main_batch)
asteroids_initial = asteroid(3, player_ship.position, main_batch)  # 3 - кол-во астероидов
game_objects = [player_ship] + asteroids_initial
asteroid_list = asteroids_initial


def check_collisions():
    hit_box = {}
    for x, y in player_ship.collision_cells():
        hit_box[x, y] = player_ship

    for ast in asteroid_list:
        for x, y in ast.collision_cells():
            if (x, y) in hit_box:
                ast.hit = True
                hit_box[x, y].hit = True
                del hit_box[x, y]
                ast.dead = True
                player_ship.opacity = 0


def update(dt):
    global obj_1, obj_2, AST, x1, x2
    for i in range(len(game_objects)):
        for j in range(i + 1, len(game_objects)):
            obj_1 = game_objects[i]
            obj_2 = game_objects[j]
    if not obj_1.dead and not obj_2.dead:
        if obj_1.collides_with(obj_2):
            obj_1.handle_collision_with(obj_2)
            obj_2.handle_collision_with(obj_1)
    for obj in game_objects:
        obj.update(dt)
    for t in [obj for obj in game_objects if obj.dead]:
        t.delete()
        game_objects.remove(t)

        del asteroid_list[:]
        asteroid_list.extend(game_objects)
        asteroid_list.pop(0)
        # print(len(asteroid_list), asteroid_list)
        AST = len(game_objects) - 1
        if AST <= 0 or num_icons - num_icon == 0:
            game_over()

    x1 += 3 * dt
    x2 += 3 * dt
    if x1 >= game_window.width:
        x1 = 0
    if x2 >= 0:
        x2 = -game_window.width

    check_collisions()


@game_window.event
def on_key_press(symbol, modifiers):
    global paused
    if symbol == key.P:
        block.reverse()
        paused = block[1]
    elif modifiers & key.MOD_CTRL:
        pass

    if symbol == key.UP:
        keys['Up'] = True
    elif symbol == key.DOWN:
        keys['Down'] = True
    elif symbol == key.LEFT:
        keys['Left'] = True
    elif symbol == key.RIGHT:
        keys['Right'] = True
    elif symbol == key.SPACE:
        keys['Fire'] = True


@game_window.event
def on_key_release(symbol, modifiers):
    if symbol == key.UP:
        keys['Up'] = False
    elif symbol == key.DOWN:
        keys['Down'] = False
    elif symbol == key.LEFT:
        keys['Left'] = False
    elif symbol == key.RIGHT:
        keys['Right'] = False
    elif symbol == key.SPACE:
        keys['Fire'] = False
    elif modifiers & key.MOD_CTRL:
        pass


@game_window.event
def on_draw():
    game_window.clear()
    star_field_image.blit(x1, 0, width=game_window.width, height=game_window.height)
    star_field_image.blit(x2, 0, width=game_window.width, height=game_window.height)
    asteroid_label.text = "Астероиды: " + str(AST)
    score_label.text = "Очки: " + str(int(SCORE))
    for i in range(num_icons - num_icon):
        player_image.blit(x=game_window.width - i * 30, y=game_window.height,
                          width=player_image.width//3, height=player_image.height//3)
    if game:
        if not paused:
            main_batch.draw()
        else:
            game_over_label.text = "ПАУЗА"
            game_over_label.draw()
            asteroid_label.draw()
            score_label.draw()
            level_label.draw()
    else:
        if SCORE > 38:
            game_over_label.text = "YOU ROCK!"
        else:
            game_over_label.text = "GAME OVER"
        game_over_label.draw()
        asteroid_label.draw()
        score_label.draw()
        level_label.draw()


if __name__ == '__main__':
    pyglet.clock.schedule_interval(update, 1 / 120.0)
    pyglet.app.run()
