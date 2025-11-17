import pygame
from config import *
from skill_effects import Projectile, AreaAttackEffect # AreaAttackEffect 임포트
import math

# 커스텀 이벤트 정의
SWORDSMAN_DASH_END = pygame.USEREVENT + 3
AUGMENT_READY = pygame.USEREVENT + 4 # 증강 선택 이벤트

class Player(pygame.sprite.Sprite):
    def __init__(self, character_key):
        super().__init__()
        
        self.character_key = character_key
        self.stats = CHARACTERS[self.character_key]
        
        # --- 기본 스탯 및 원본 저장 ---
        self.hp = self.stats['hp']
        self.max_hp = self.stats['hp']
        self.base_attack_power = self.stats['attack_power']
        self.attack_power = self.base_attack_power
        self.base_attack_speed = self.stats['attack_speed']
        self.attack_speed = self.base_attack_speed
        self.base_move_speed = self.stats['move_speed']
        self.move_speed = self.base_move_speed
        self.base_splash_radius = self.stats.get('splash_radius', 0)
        self.splash_radius = self.base_splash_radius
        
        # --- 레벨 및 경험치 ---
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 1000

        # --- 대쉬 스탯 ---
        self.dash_charges = 3
        self.max_dash_charges = 3
        self.dash_charge_time = 5000 # 5초
        self.last_dash_charge_time = pygame.time.get_ticks()
        self.is_dashing = False
        self.is_invincible = False
        self.dash_start_time = 0
        self.dash_duration = 150 # 0.15초 대쉬
        self.dash_speed_multiplier = 4 # 기본 이동 속도의 4배
        self.dash_direction = pygame.math.Vector2(0, 0) # 대쉬 방향

        # --- 스킬 스탯 ---
        self.skill_cooldown = self.stats.get('skill_cooldown', 99999)
        self.last_skill_time = -self.skill_cooldown # 시작하자마자 사용 가능하도록
        self.is_skill_active = False
        self.skill_start_time = 0
        self.skill_duration = self.stats.get('skill_duration', 0)

        # --- 기존 대쉬 스탯 (검사 스킬용)은 새로운 범용 대쉬 스탯으로 통합되었으므로 삭제 ---


        # --- 이미지 및 위치 ---
        try:
            image_key = "swordman" if self.character_key == "swordsman" else self.character_key
            image_path = f"src/assets/images/{image_key}.png"
            original_image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(original_image, (50, 50))
        except pygame.error as e:
            print(f"플레이어 이미지를 불러올 수 없습니다: {e}")
            self.image = pygame.Surface((50, 50))
            self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        
        self.pos = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(0, 0)

        # --- 조준 및 발사 모드 ---
        self.aim_mode = 'auto_target'  # 'auto_target' 또는 'manual_aim'
        self.manual_fire_mode = 'click_fire' # 'click_fire' 또는 'cursor_auto_fire'
        self.last_attack_time = 0 # 마지막 공격 시간 (쿨다운용)

        # --- 증강 정보 ---
        self.chosen_augments = []

    def switch_aim_mode(self):
        if self.aim_mode == 'auto_target':
            self.aim_mode = 'manual_aim'
        else:
            self.aim_mode = 'auto_target'
        print(f"조준 모드 변경: {self.aim_mode}")

    def switch_manual_fire_mode(self):
        if self.manual_fire_mode == 'click_fire':
            self.manual_fire_mode = 'cursor_auto_fire'
        else:
            self.manual_fire_mode = 'click_fire'
        print(f"수동 발사 모드 변경: {self.manual_fire_mode}")

    def activate_skill(self, all_sprites=None, enemies=None):
        now = pygame.time.get_ticks()
        new_projectiles = []
        new_skill_effects = []

        if now - self.last_skill_time >= self.skill_cooldown:
            self.last_skill_time = now
            print(f"{self.stats['name']} 스킬 발동!")

            # 바이킹 스킬: 광폭화 (스탯 버프)
            if self.character_key == 'viking':
                self.is_skill_active = True
                self.skill_start_time = now
                buff_stats = self.stats['skill_stats']
                self.move_speed = buff_stats['move_speed']
                self.attack_power = buff_stats['attack_power']
                self.attack_speed = buff_stats['attack_speed']
                # 공격 속도 변경을 main loop에 알려야 함
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'action': 'ATTACK_SPEED_CHANGED'}))
            
            # 마법사 스킬: 마력 증폭 (스탯 버프)
            elif self.character_key == 'wizard':
                self.is_skill_active = True
                self.skill_start_time = now
                buff_stats = self.stats['skill_stats']
                self.attack_power = buff_stats['attack_power']
                self.splash_radius = self.base_splash_radius * 1.5 # 스플래쉬 범위 1.5배 증가
                print(f"마력 증폭! 공격력: {self.attack_power}, 스플래쉬 범위: {self.splash_radius}")

            # 암살자 스킬: 전방위 표창 발사
            elif self.character_key == 'assassin':
                self.is_skill_active = True
                self.skill_start_time = now
                skill_damage = self.stats['skill_damage']
                num_projectiles = 8 # 8방향으로 발사
                projectile_speed = 20 # 표창 속도
                projectile_image_path = "src/assets/images/shuriken.png" # 표창 이미지 경로 (추후 추가 필요)

                for i in range(num_projectiles):
                    angle = i * (360 / num_projectiles)
                    rad_angle = math.radians(angle)
                    target_x = self.pos.x + math.cos(rad_angle) * 1000 # 화면 밖으로 충분히 멀리
                    target_y = self.pos.y + math.sin(rad_angle) * 1000
                    
                    projectile = Projectile(self.pos.x, self.pos.y, target_x, target_y, 
                                            projectile_speed, skill_damage, projectile_image_path)
                    new_projectiles.append(projectile)
                print(f"암살자 스킬 발동! {num_projectiles}개의 표창 발사!")
            
            # 검사 스킬: 대쉬하며 범위 공격
            elif self.character_key == 'swordsman':
                self.is_skill_active = True
                self.is_dashing = True
                self.skill_start_time = now
                self.dash_start_time = now
                self.is_invincible = True # 대쉬 중 무적
                
                # 대쉬 방향 설정: 현재 이동 방향이 있으면 그 방향으로, 없으면 기본 방향 (오른쪽)
                if self.velocity.length() > 0:
                    self.dash_direction = self.velocity.normalize()
                else:
                    self.dash_direction = pygame.math.Vector2(1, 0) # 기본 오른쪽
                print("검사 스킬 발동! 대쉬!")
            
            # 궁수 스킬: 거대한 화살로 범위 공격
            elif self.character_key == 'archer':
                self.is_skill_active = True
                self.skill_start_time = now
                skill_damage = self.stats['skill_damage']
                area_radius = 150 # 궁수 스킬 범위 반경
                
                # 가장 가까운 적 찾기
                nearest_enemy = None
                min_dist = float('inf')
                if enemies:
                    for enemy in enemies:
                        dist = self.pos.distance_to(enemy.pos)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_enemy = enemy
                
                if nearest_enemy:
                    # 가장 가까운 적 위치에 범위 공격 생성
                    area_effect = AreaAttackEffect(nearest_enemy.pos.x, nearest_enemy.pos.y, 
                                                   area_radius, skill_damage, 500, GREEN) # 0.5초 지속, 초록색
                    new_skill_effects.append(area_effect)
                    print(f"궁수 스킬 발동! {nearest_enemy.enemy_key} 위치에 범위 공격! 데미지: {skill_damage}")
                else:
                    print("궁수 스킬 발동 실패: 주변에 적이 없습니다.")


        return new_projectiles, new_skill_effects

    def deactivate_skill_effects(self):
        # 바이킹 스킬: 스탯 원래대로
        if self.character_key == 'viking':
            self.move_speed = self.base_move_speed
            self.attack_power = self.base_attack_power
            self.attack_speed = self.base_attack_speed
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'action': 'ATTACK_SPEED_CHANGED'}))
            print("바이킹 스킬 종료")
        # 마법사 스킬: 스탯 원래대로
        elif self.character_key == 'wizard':
            self.attack_power = self.base_attack_power
            self.splash_radius = self.base_splash_radius
            print("마법사 스킬 종료")

    def gain_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_next_level:
            self.level_up()

    def level_up(self):
        self.exp -= self.exp_to_next_level
        self.level += 1
        level_tier = (self.level - 1) // 10
        self.exp_to_next_level = (level_tier + 1) * 1000
        print(f"레벨 업! 현재 레벨: {self.level}")
        if self.level % 10 == 0:
            pygame.event.post(pygame.event.Event(AUGMENT_READY, {'player': self})) # 증강 선택 이벤트 발생

    def apply_augment(self, augment_key):
        self.chosen_augments.append(augment_key)
        augment = AUGMENTS[augment_key]
        print(f"증강 적용: {augment['name']}")
        for key, value in augment['effect'].items():
            if key == 'max_hp_multiplier':
                self.max_hp *= value
                self.hp = self.max_hp # 체력 증강 시 현재 체력도 모두 회복
                print(f"최대 체력 증가 -> {self.max_hp}")
            elif key == 'attack_power_multiplier':
                self.base_attack_power *= value
                self.attack_power = self.base_attack_power
                print(f"기본 공격력 증가 -> {self.base_attack_power}")
            elif key == 'move_speed_multiplier':
                self.base_move_speed *= value
                self.move_speed = self.base_move_speed
                print(f"기본 이동 속도 증가 -> {self.base_move_speed}")
            elif key == 'skill_cooldown_multiplier':
                self.skill_cooldown *= value
                print(f"스킬 쿨다운 감소 -> {self.skill_cooldown / 1000}초")
            elif key == 'splash_radius_multiplier':
                self.base_splash_radius *= value
                self.splash_radius = self.base_splash_radius
                print(f"스플래쉬 범위 증가 -> {self.base_splash_radius}")

    def dash(self, mouse_pos):
        if self.dash_charges > 0 and not self.is_dashing:
            self.is_dashing = True
            self.is_invincible = True
            self.dash_charges -= 1
            self.dash_start_time = pygame.time.get_ticks()
            
            # 1. 이동 중일 경우, 해당 방향으로 대쉬
            if self.velocity.length() > 0:
                self.dash_direction = self.velocity.normalize()
            # 2. 멈춰있을 경우, 마우스 커서 방향으로 대쉬
            else:
                mouse_vec = pygame.math.Vector2(mouse_pos)
                self.dash_direction = (mouse_vec - self.pos).normalize() if (mouse_vec - self.pos).length() > 0 else pygame.math.Vector2(1, 0)


    def update(self):
        now = pygame.time.get_ticks()

        # 대쉬 충전
        if self.dash_charges < self.max_dash_charges and now - self.last_dash_charge_time > self.dash_charge_time:
            self.dash_charges += 1
            self.last_dash_charge_time = now
        
        # 스킬 지속시간 처리
        if self.is_skill_active and now - self.skill_start_time > self.skill_duration:
            self.is_skill_active = False
            self.deactivate_skill_effects()

        # 대쉬 상태 처리 (범용)
        if self.is_dashing:
            if now - self.dash_start_time > self.dash_duration:
                self.is_dashing = False
                self.is_invincible = False
                # 검사 스킬의 경우, 스킬 플래그도 비활성화
                if self.character_key == 'swordsman' and self.is_skill_active:
                    self.is_skill_active = False 
                    pygame.event.post(pygame.event.Event(SWORDSMAN_DASH_END, {
                        'pos': self.pos,
                        'skill_damage': self.stats['skill_damage']
                    }))
            else:
                # 대쉬 방향으로 이동
                self.pos += self.dash_direction * self.base_move_speed * self.dash_speed_multiplier * (1/FPS)
                self.rect.center = self.pos
                return # 대쉬 중에는 일반 이동 처리 건너뛰기

        # 일반 이동 처리
        keys = pygame.key.get_pressed()
        self.velocity.x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.velocity.y = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        if self.velocity.length() > 0:
            self.velocity.normalize_ip()
        
        self.pos += self.velocity * self.move_speed
        
        if self.pos.x < 0: self.pos.x = 0
        if self.pos.x > SCREEN_WIDTH: self.pos.x = SCREEN_WIDTH
        if self.pos.y < 0: self.pos.y = 0
        if self.pos.y > SCREEN_HEIGHT: self.pos.y = SCREEN_HEIGHT
            
        self.rect.center = self.pos

    def draw(self, surface):
        surface.blit(self.image, self.rect)
