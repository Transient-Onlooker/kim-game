import pygame
import sys
import random
from config import *
from player import Player, SWORDSMAN_DASH_END, AUGMENT_READY
from enemy import Enemy
from weapon import Weapon
from skill_effects import Projectile, AreaAttackEffect
from boss import Boss, STAGE_CLEAR

# --- 초기화 ---
pygame.init()
try:
    font_path = "src/assets/fonts/Pretendard-Light.otf"
    TITLE_FONT = pygame.font.Font(font_path, 74)
    DESC_FONT = pygame.font.Font(font_path, 36)
    STATS_FONT = pygame.font.Font(font_path, 28)
except FileNotFoundError:
    print(f"'{font_path}' 폰트를 찾을 수 없습니다. 기본 폰트로 대체합니다.")
    TITLE_FONT = pygame.font.Font(None, 80)
    DESC_FONT = pygame.font.Font(None, 40)
    STATS_FONT = pygame.font.Font(None, 32)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("김준우 게임")

# --- UI 및 그리기 함수 ---

class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False

    def draw(self, surface, font=DESC_FONT):
        draw_color = self.hover_color if self.is_hovered else self.color
        text_surf = font.render(self.text, True, BLACK)
        
        # 텍스트 크기에 맞춰 버튼 크기 동적 조절
        self.rect.width = max(self.rect.width, text_surf.get_width() + 40)
        self.rect.height = max(self.rect.height, text_surf.get_height() + 20)

        pygame.draw.rect(surface, draw_color, self.rect, border_radius=10)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            if self.action:
                return self.action
        return None

def draw_text(text, font, color, surface, x, y, center=False):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

def draw_hud(surface, player, current_stage_index, kill_count, is_boss_spawned, enemies):
    stage_name = STAGES[current_stage_index]['name']
    if is_boss_spawned:
        stage_text = f"Stage: {stage_name} - BOSS"
    else:
        stage_text = f"Stage: {stage_name} ({kill_count} / 100)"
    draw_text(stage_text, DESC_FONT, WHITE, surface, SCREEN_WIDTH / 2, 30, center=True)

    # 보스 체력 바 그리기
    if is_boss_spawned:
        boss = next((enemy for enemy in enemies if isinstance(enemy, Boss)), None)
        if boss:
            boss_bar_width = SCREEN_WIDTH * 0.6
            boss_bar_height = 20
            boss_bar_x = (SCREEN_WIDTH - boss_bar_width) / 2
            boss_bar_y = 60 # 스테이지 텍스트 아래

            boss_health_ratio = boss.hp / boss.max_hp
            
            # 배경
            bg_rect = pygame.Rect(boss_bar_x, boss_bar_y, boss_bar_width, boss_bar_height)
            pygame.draw.rect(surface, GRAY, bg_rect)
            
            # 체력
            fill_rect = pygame.Rect(boss_bar_x, boss_bar_y, boss_bar_width * boss_health_ratio, boss_bar_height)
            pygame.draw.rect(surface, PURPLE, fill_rect)
            
            # 테두리
            pygame.draw.rect(surface, WHITE, bg_rect, 2)
            
            # 보스 이름
            boss_name_text = f"{boss.stats['name']}"
            draw_text(boss_name_text, STATS_FONT, WHITE, surface, SCREEN_WIDTH / 2, boss_bar_y + boss_bar_height + 15, center=True)

    bar_length, bar_height = 400, 30
    hp_x, hp_y = 10, 10
    current_hp = max(0, player.hp)
    fill_ratio = current_hp / player.max_hp
    bg_rect = pygame.Rect(hp_x, hp_y, bar_length, bar_height)
    fill_rect = pygame.Rect(hp_x, hp_y, bar_length * fill_ratio, bar_height)
    pygame.draw.rect(surface, GRAY, bg_rect)
    pygame.draw.rect(surface, GREEN, fill_rect)
    pygame.draw.rect(surface, WHITE, bg_rect, 2)
    hp_text = f"HP: {int(current_hp)} / {int(player.max_hp)}"
    draw_text(hp_text, STATS_FONT, WHITE, surface, hp_x + bar_length + 10, hp_y)

    exp_y = hp_y + bar_height + 5
    exp_bar_height = bar_height - 10
    exp_ratio = player.exp / player.exp_to_next_level
    exp_bg_rect = pygame.Rect(hp_x, exp_y, bar_length, exp_bar_height)
    exp_fill_rect = pygame.Rect(hp_x, exp_y, bar_length * exp_ratio, exp_bar_height)
    pygame.draw.rect(surface, GRAY, exp_bg_rect)
    pygame.draw.rect(surface, BLUE, exp_fill_rect)
    pygame.draw.rect(surface, WHITE, exp_bg_rect, 2)
    exp_text = f"EXP: {int(player.exp)} / {int(player.exp_to_next_level)}"
    draw_text(exp_text, STATS_FONT, WHITE, surface, hp_x + bar_length + 10, exp_y)

    level_text = f"Level: {player.level}"
    draw_text(level_text, DESC_FONT, WHITE, surface, hp_x, exp_y + exp_bar_height + 5)

    # --- 조준 및 발사 모드 표시 (레벨 아래 중앙) ---
    if player.aim_mode == 'auto_target':
        mode_text = "Aim: Auto Target"
    else: # manual_aim
        manual_mode_text = player.manual_fire_mode.replace('_', ' ').replace('fire', '').capitalize()
        mode_text = f"Aim: Manual ({manual_mode_text.strip()})"
    draw_text(mode_text, STATS_FONT, WHITE, surface, SCREEN_WIDTH / 2, exp_y + exp_bar_height + 15, center=True)
    
    jump_text = f"Jumps: {player.jump_charges}"
    draw_text(jump_text, DESC_FONT, WHITE, surface, SCREEN_WIDTH - 200, 10)
    
    now = pygame.time.get_ticks()
    time_since_skill = now - player.last_skill_time
    if time_since_skill >= player.skill_cooldown:
        skill_text = "Skill: Ready"
        skill_color = GREEN
    else:
        remaining_cd = (player.skill_cooldown - time_since_skill) / 1000
        skill_text = f"Skill: {remaining_cd:.1f}s"
        skill_color = GRAY
    draw_text(skill_text, DESC_FONT, skill_color, surface, SCREEN_WIDTH - 200, 50)


# --- 게임 상태 관리 ---

def character_selection_screen():
    buttons = [Button(CHARACTERS[key]["name"], 150, 200 + i * 80, 250, 60, LIGHT_GRAY, WHITE, key) for i, key in enumerate(CHARACTERS.keys())]
    hovered_character_key = None
    while True:
        mouse_pos = pygame.mouse.get_pos()
        hovered_character_key = next((btn.action for btn in buttons if btn.rect.collidepoint(mouse_pos)), None)

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return None
            for btn in buttons:
                result = btn.handle_event(event)
                if result: return result

        screen.fill(BLACK)
        draw_text("캐릭터 선택", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 100, center=True)
        for btn in buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)
        if hovered_character_key:
            char_info = CHARACTERS[hovered_character_key]
            info_x, info_y = 500, 250
            draw_text(f"이름: {char_info['name']}", DESC_FONT, WHITE, screen, info_x, info_y)
            draw_text(f"체력: {char_info['hp']}", STATS_FONT, WHITE, screen, info_x, info_y + 60)
            draw_text(f"공격력: {char_info['attack_power']}", STATS_FONT, WHITE, screen, info_x, info_y + 100)
            draw_text(f"공격 속도: {char_info['attack_speed']}초", STATS_FONT, WHITE, screen, info_x, info_y + 140)
            draw_text(f"이동 속도: {char_info['move_speed']}", STATS_FONT, WHITE, screen, info_x, info_y + 180)
            draw_text(f"특징: {char_info['description']}", STATS_FONT, WHITE, screen, info_x, info_y + 240)
            draw_text(char_info['skill_text'], STATS_FONT, GREEN, screen, info_x, info_y + 280)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

def augment_selection_screen(player):
    available_augments = list(AUGMENTS.keys())
    chosen_augment_keys = random.sample(available_augments, 3)

    augment_buttons = []
    button_width, button_height = 400, 150
    start_x = (SCREEN_WIDTH - button_width) / 2
    start_y = (SCREEN_HEIGHT - (button_height * 3 + 20 * 2)) / 2

    for i, key in enumerate(chosen_augment_keys):
        augment = AUGMENTS[key]
        button_text = f"{augment['name']}: {augment['description']}"
        button = Button(button_text, start_x, start_y + i * (button_height + 20), button_width, button_height, LIGHT_GRAY, WHITE, key)
        augment_buttons.append(button)

    selecting = True
    while selecting:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for btn in augment_buttons:
                result = btn.handle_event(event)
                if result:
                    player.apply_augment(result)
                    selecting = False
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        draw_text("증강 선택", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 150, center=True)
        for btn in augment_buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

def view_augments_screen(player):
    back_button = Button("돌아가기", SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT - 100, 200, 50, LIGHT_GRAY, WHITE, "back")
    
    viewing = True
    while viewing:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit_game"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                viewing = False
            if back_button.handle_event(event):
                viewing = False

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))

        draw_text("획득한 증강", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 100, center=True)
        
        if not player.chosen_augments:
            draw_text("아직 획득한 증강이 없습니다.", DESC_FONT, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, center=True)
        else:
            for i, augment_key in enumerate(player.chosen_augments):
                augment = AUGMENTS[augment_key]
                augment_text = f"- {augment['name']}: {augment['description']}"
                draw_text(augment_text, STATS_FONT, WHITE, screen, 300, 200 + i * 50)

        back_button.is_hovered = back_button.rect.collidepoint(mouse_pos)
        back_button.draw(screen)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)
    return "pause"

def pause_menu(player):
    paused = True
    menu_options = {
        "continue": "계속하기",
        "view_augments": "증강 보기",
        "change_character": "캐릭터 바꾸기",
        "exit_game": "게임 종료하기"
    }
    
    buttons = []
    button_y = 300
    for action, text in menu_options.items():
        button = Button(text, SCREEN_WIDTH / 2 - 150, button_y, 300, 60, LIGHT_GRAY, WHITE, action)
        buttons.append(button)
        button_y += 80

    while paused:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit_game"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "continue"
            
            for btn in buttons:
                result = btn.handle_event(event)
                if result == "continue":
                    return "continue"
                elif result == "exit_game":
                    return "exit_game"
                elif result == "change_character":
                    return "change_character"
                elif result == "view_augments":
                    # 증강 보기 화면에서 "exit_game"이 반환될 수 있음
                    if view_augments_screen(player) == "exit_game":
                        return "exit_game"

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        draw_text("일시정지", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 150, center=True)
        for btn in buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

def game_play_loop(selected_character_key):
    all_sprites, enemies, weapons = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
    player = Player(selected_character_key)
    all_sprites.add(player)
    all_projectiles = pygame.sprite.Group()
    all_skill_effects = pygame.sprite.Group()

    current_stage_index = 0
    stage_level = 1
    kill_count = 0
    is_boss_spawned = False
    spawn_interval = 1000

    ADD_ENEMY = pygame.USEREVENT + 1
    pygame.time.set_timer(ADD_ENEMY, spawn_interval)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return "exit_game" # 게임 전체 종료를 위해
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = pause_menu(player)
                    if action == "exit_game":
                        running = False
                        return "exit_game"
                    elif action == "change_character":
                        running = False
                        return "change_character"
                if event.key == pygame.K_SPACE:
                    player.jump()
                if event.key == pygame.K_q:
                    new_projectiles, new_skill_effects = player.activate_skill(enemies=enemies)
                    all_projectiles.add(new_projectiles)
                    all_sprites.add(new_projectiles)
                    all_skill_effects.add(new_skill_effects)
                    all_sprites.add(new_skill_effects)
                if event.key == pygame.K_TAB: # TAB 키로 조준 모드 전환
                    player.switch_aim_mode()
                if event.key == pygame.K_h: # 'H' 키로 수동 발사 모드 전환
                    if player.aim_mode == 'manual_aim': # 수동 조준 모드일 때만 작동
                        player.switch_manual_fire_mode()
            
            if event.type == ADD_ENEMY and not is_boss_spawned:
                stage_info = STAGES[current_stage_index]
                enemy_key = random.choice(stage_info["enemies"])
                new_enemy = Enemy(enemy_key, player, stage_level)
                enemies.add(new_enemy)
                all_sprites.add(new_enemy)
            
            if event.type == SWORDSMAN_DASH_END:
                pos = event.dict['pos']
                skill_damage = event.dict['skill_damage']
                area_radius = 100
                area_effect = AreaAttackEffect(pos.x, pos.y, area_radius, skill_damage, 200)
                all_skill_effects.add(area_effect)
                all_sprites.add(area_effect)
            
            if event.type == AUGMENT_READY:
                augment_selection_screen(event.player)
                pygame.time.set_timer(PLAYER_ATTACK, 0)
                pygame.time.set_timer(PLAYER_ATTACK, int(player.attack_speed * 1000))
            
            if event.type == STAGE_CLEAR:
                player.level_up()
                current_stage_index = (current_stage_index + 1) % len(STAGES)
                stage_level += 1
                kill_count = 0
                is_boss_spawned = False
                for enemy in enemies:
                    enemy.kill()
                spawn_interval = max(200, 1000 - (stage_level - 1) * 100)
                pygame.time.set_timer(ADD_ENEMY, 0)
                pygame.time.set_timer(ADD_ENEMY, int(spawn_interval))
                print(f"새로운 스폰 간격: {spawn_interval}ms")

        # --- 공격 로직 (이벤트 루프 밖에서 항상 체크) ---
        now = pygame.time.get_ticks()
        can_attack = now - player.last_attack_time > player.attack_speed * 1000
        
        fire_request = False
        target_pos = None
        use_nearest_enemy = False

        # 1. 조준 모드에 따라 분기
        if player.aim_mode == 'auto_target':
            fire_request = True
            use_nearest_enemy = True
        
        elif player.aim_mode == 'manual_aim':
            # 2. 수동 조준 모드 내에서 발사 방식에 따라 분기
            if player.manual_fire_mode == 'cursor_auto_fire':
                fire_request = True
                target_pos = pygame.mouse.get_pos()
            
            elif player.manual_fire_mode == 'click_fire':
                if pygame.mouse.get_pressed()[0]: # 마우스 왼쪽 버튼 누름 확인
                    fire_request = True
                    target_pos = pygame.mouse.get_pos()

        # 3. 발사 결정
        if fire_request and can_attack:
            player.last_attack_time = now
            
            if use_nearest_enemy:
                if enemies: # 공격할 적이 있는지 확인
                    new_weapon = Weapon(player, enemies=enemies)
                    weapons.add(new_weapon)
                    all_sprites.add(new_weapon)
            elif target_pos:
                new_weapon = Weapon(player, target_pos=target_pos)
                weapons.add(new_weapon)
                all_sprites.add(new_weapon)

        all_sprites.update()
        all_projectiles.update()
        all_skill_effects.update()

        hits = pygame.sprite.groupcollide(weapons, enemies, True, False)
        for weapon, hit_enemies_list in hits.items():
            primary_target = hit_enemies_list[0]
            if player.splash_radius > 0:
                splash_rect = pygame.Rect(0, 0, player.splash_radius * 2, player.splash_radius * 2)
                splash_rect.center = primary_target.rect.center
                enemies_in_splash = [enemy for enemy in enemies if splash_rect.colliderect(enemy.rect)]
                for enemy in enemies_in_splash:
                    exp_gain = enemy.take_damage(player.attack_power)
                    if exp_gain > 0:
                        player.gain_exp(exp_gain)
                        kill_count += 1
            else:
                exp_gain = primary_target.take_damage(player.attack_power)
                if exp_gain > 0:
                    player.gain_exp(exp_gain)
                    kill_count += 1
        
        projectile_hits = pygame.sprite.groupcollide(all_projectiles, enemies, True, False)
        for projectile, hit_enemies_list in projectile_hits.items():
            for enemy in hit_enemies_list:
                exp_gain = enemy.take_damage(projectile.damage)
                if exp_gain > 0:
                    player.gain_exp(exp_gain)
                    kill_count += 1
        
        skill_effect_hits = pygame.sprite.groupcollide(all_skill_effects, enemies, False, False)
        for skill_effect, hit_enemies_list in skill_effect_hits.items():
            if isinstance(skill_effect, AreaAttackEffect) and not skill_effect.has_damaged:
                for enemy in hit_enemies_list:
                    exp_gain = enemy.take_damage(skill_effect.damage)
                    if exp_gain > 0:
                        player.gain_exp(exp_gain)
                        kill_count += 1
                skill_effect.has_damaged = True

        if not player.is_invincible:
            collided_enemies = pygame.sprite.spritecollide(player, enemies, True)
            for enemy in collided_enemies:
                player.hp -= enemy.attack_power

        if player.hp <= 0:
            print("플레이어가 사망했습니다. 게임 오버!")
            running = False
            return "change_character" # 게임 오버 시 캐릭터 선택 화면으로

        if kill_count >= 100 and not is_boss_spawned:
            is_boss_spawned = True
            boss_key = STAGES[current_stage_index]["boss"]
            boss = Boss(boss_key, player, stage_level)
            enemies.add(boss)
            all_sprites.add(boss)

        screen.fill(BLACK)
        all_sprites.draw(screen)

        # 모든 적의 체력 바 그리기 (보스 제외)
        for enemy in enemies:
            if not isinstance(enemy, Boss):
                enemy.draw_health_bar(screen)

        draw_hud(screen, player, current_stage_index, kill_count, is_boss_spawned, enemies)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)
    
    return "continue" # 일반적인 루프 종료 (예: 캐릭터 변경)

def main():
    while True:
        selected_character = character_selection_screen()
        if not selected_character:
            break # 게임 완전 종료
        
        action = game_play_loop(selected_character)
        if action == "exit_game":
            break # 게임 완전 종료

if __name__ == '__main__':
    main()
    pygame.quit()
    sys.exit()