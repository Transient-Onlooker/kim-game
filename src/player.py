import pygame
from config import *
from skill_effects import Projectile, AreaAttackEffect # AreaAttackEffect 임포트
from utils import load_image
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
        self.defense = 0 # 방어력 스탯 추가
        
        # --- 임시 스탯 버프 ---
        # 예: {"attack_power": {"amount": 50, "expire_level": 25}}
        self.temporary_boosts = {}
        
        # --- 레벨 및 경험치 ---
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 1000

        # --- 대쉬 스탯 ---
        self.dash_charges = 3
        self.max_dash_charges = 3
        self.dash_charge_time = 5000 # 5초
        self.last_dash_recharge_start_time = 0 # 대쉬 쿨타임 시작 시간
        self.is_dashing = False
        self.is_invincible = False
        self.dash_start_time = 0
        self.dash_duration = 150 # 0.15초 대쉬 (무적 시간)
        # self.dash_speed_multiplier = 4 # 사용되지 않음
        # self.dash_direction = pygame.math.Vector2(0, 0) # 사용되지 않음

        # --- 스킬 스탯 ---
        self.skill_cooldown = self.stats.get('skill_cooldown', 99999)
        self.last_skill_time = -self.skill_cooldown # 시작하자마자 사용 가능하도록
        self.is_skill_active = False
        self.skill_start_time = 0
        self.skill_duration = self.stats.get('skill_duration', 0)

        # --- 기존 대쉬 스탯 (검사 스킬용)은 새로운 범용 대쉬 스탯으로 통합되었으므로 삭제 ---


        # --- 이미지 및 위치 ---
        image_key = "swordman" if self.character_key == "swordsman" else self.character_key
        image_path = f"src/assets/images/{image_key}.png"
        self.image = load_image(image_path, scale=(50, 50))

        if self.character_key == 'archer':
            self.image_idle = self.image
            self.image_dash = load_image('src/assets/images/archer_2.png', scale=(50, 50))
            self.image_attack = load_image('src/assets/images/archer_attack.png', scale=(50, 50))
            
        if self.character_key == 'assassin':
            self.image_idle = self.image # assassin.png (기본 이미지)
            self.image_walk = load_image('src/assets/images/assassin_walk.png', scale=(50, 50))
            self.image_attack = load_image('src/assets/images/assassin_attack.png', scale=(50, 50))

        elif self.character_key == 'knight':
            self.image_idle = self.image # knight.png (기본 이미지)
            self.image_walk = load_image('src/assets/images/knight_walk.png', scale=(50, 50))
            self.image_attack = load_image('src/assets/images/knight_attack.png', scale=(50, 50))

        elif self.character_key == 'viking':
            self.image_idle = self.image # viking.png (기본 이미지)
            self.image_walk = self.image # viking.png (걷는 이미지도 동일)
            self.image_attack = load_image('src/assets/images/viking_attack.png', scale=(50, 50))

        elif self.character_key == 'wizard':
            self.image_idle = self.image # wizard.png (기본 이미지)
            self.image_walk = self.image # wizard.png (걷는 이미지도 동일)
            self.image_attack = load_image('src/assets/images/wizard_attack.png', scale=(50, 50))

        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        
        self.pos = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(0, 0)

        # --- 조준 및 발사 모드 ---
        self.aim_mode = 'auto_target'  # 'auto_target' 또는 'manual_aim'
        self.manual_fire_mode = 'click_fire' # 'click_fire' 또는 'cursor_auto_fire'
        self.last_attack_time = 0 # 마지막 공격 시간 (쿨다운용)

        # --- 증강 정보 ---
        self.chosen_augments = []
        self.coins = 0

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

    def activate_skill(self, all_sprites=None, enemies=None, mouse_pos=None):
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
            
            # 검사 스킬: 대쉬하며 범위 공격 (즉시 발동)
            elif self.character_key == 'swordsman':
                print("검사 스킬 발동! 대쉬!")
                
                # 1. 대쉬 방향 결정 (일반 대쉬와 동일한 로직)
                direction = pygame.math.Vector2(0, 0)
                if self.velocity.length() > 0:
                    direction = self.velocity.normalize()
                elif mouse_pos: # 멈춰있을 경우, 마우스 커서 방향으로
                    mouse_vec = pygame.math.Vector2(mouse_pos)
                    direction = mouse_vec - self.pos
                    if direction.length() == 0:
                        direction = pygame.math.Vector2(1, 0) # 기본 방향 (오른쪽)
                    else:
                        direction.normalize_ip()
                else: # mouse_pos가 없는 비상상황
                    direction = pygame.math.Vector2(1, 0) # 기본 방향 (오른쪽)

                # 2. 순간이동
                skill_dash_distance = 400 # 일반 대쉬보다 긴 거리
                self.pos += direction * skill_dash_distance
                
                # 화면 밖으로 나가지 않도록 보정
                self.pos.x = max(0, min(SCREEN_WIDTH, self.pos.x))
                self.pos.y = max(0, min(SCREEN_HEIGHT, self.pos.y))
                self.rect.center = self.pos

                # 3. 도착 지점에 범위 공격 이펙트 생성
                skill_damage = self.stats['skill_damage']
                area_radius = 120 # 스킬 범위
                area_effect = AreaAttackEffect(self.pos.x, self.pos.y, area_radius, skill_damage, 300) # 0.3초 지속
                new_skill_effects.append(area_effect)
            
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

    def take_damage(self, amount):
        """플레이어가 데미지를 받을 때 방어력을 적용하여 체력을 감소시킵니다."""
        actual_damage = max(1, amount - self.defense) # 최소 1의 데미지는 받도록
        self.hp -= actual_damage

    def level_up(self):
        self.exp -= self.exp_to_next_level
        self.level += 1
        level_tier = (self.level - 1) // 10
        self.exp_to_next_level = (level_tier + 1) * 1000
        print(f"레벨 업! 현재 레벨: {self.level}")

        # 레벨업 스탯 증가 적용
        self.max_hp += PLAYER_HP_PER_LEVEL
        self.hp = self.max_hp # 최대 체력 증가 시 현재 체력도 최대치로 회복
        self.base_attack_power += PLAYER_ATTACK_POWER_PER_LEVEL
        self.attack_power = self.base_attack_power # 기본 공격력도 함께 업데이트
        self.defense += PLAYER_DEFENSE_PER_LEVEL
        self.base_move_speed *= PLAYER_MOVE_SPEED_PER_LEVEL_MULTIPLIER
        self.move_speed = self.base_move_speed # 기본 이동 속도도 함께 업데이트
        print(f"  - 최대 체력: {self.max_hp}, 공격력: {self.attack_power}, 방어력: {self.defense}, 이동 속도: {self.move_speed:.2f}")

        # 만료된 임시 버프 확인 및 제거
        expired_boosts = []
        for stat, boost_info in self.temporary_boosts.items():
            if self.level >= boost_info["expire_level"]:
                expired_boosts.append(stat)
        
        for stat in expired_boosts:
            boost_amount = self.temporary_boosts[stat]["amount"]
            current_value = getattr(self, stat)
            setattr(self, stat, current_value - boost_amount)
            print(f"{stat} 버프가 만료되었습니다. (감소량: {boost_amount})")
            del self.temporary_boosts[stat]

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
            # 쿨타임 타이머 시작 (최대치일 때만)
            if self.dash_charges == self.max_dash_charges:
                self.last_dash_recharge_start_time = pygame.time.get_ticks()

            self.is_dashing = True
            self.is_invincible = True
            self.dash_charges -= 1
            self.dash_start_time = pygame.time.get_ticks()
            
            dash_distance = 250 
            direction = pygame.math.Vector2(0, 0)

            # 1. 이동 중일 경우 (WASD), 해당 방향으로 대쉬
            if self.velocity.length() > 0:
                direction = self.velocity.normalize()
            # 2. 멈춰있을 경우, 마우스 커서 방향으로 대쉬
            else:
                mouse_vec = pygame.math.Vector2(mouse_pos)
                direction = mouse_vec - self.pos
                if direction.length() == 0:
                    direction = pygame.math.Vector2(1, 0) # 기본 방향 (오른쪽)
                else:
                    direction.normalize_ip()

            # 결정된 방향으로 즉시 이동 (점멸)
            self.pos += direction * dash_distance
            
            # 화면 밖으로 나가지 않도록 보정
            self.pos.x = max(0, min(SCREEN_WIDTH, self.pos.x))
            self.pos.y = max(0, min(SCREEN_HEIGHT, self.pos.y))
            
            self.rect.center = self.pos


    def update(self):
        now = pygame.time.get_ticks()

        # 대쉬 충전
        if self.dash_charges < self.max_dash_charges:
            if now - self.last_dash_recharge_start_time > self.dash_charge_time:
                self.dash_charges += 1
                self.last_dash_recharge_start_time = now # 다음 충전까지의 타이머 다시 시작
        
        # 스킬 지속시간 처리
        if self.is_skill_active and now - self.skill_start_time > self.skill_duration:
            self.is_skill_active = False
            self.deactivate_skill_effects()

        # 대쉬 상태 처리 (범용) -> 이제 무적 시간 및 스킬 후처리용
        if self.is_dashing:
            # 대쉬는 즉시 발동되지만, 짧은 시간 동안 무적 상태와 재사용 방지를 유지
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
            
        # 궁수 애니메이션 상태 업데이트
        if self.character_key == 'archer':
            if self.is_skill_active:
                self.image = self.image_attack
            elif self.is_dashing:
                self.image = self.image_dash
            else:
                self.image = self.image_idle
        
        # 암살자 애니메이션 상태 업데이트
        elif self.character_key == 'assassin':
            if self.is_skill_active:
                self.image = self.image_attack
            elif self.velocity.length() > 0 or self.is_dashing:
                self.image = self.image_walk
            else:
                self.image = self.image_idle

        # 나이트 애니메이션 상태 업데이트
        elif self.character_key == 'knight':
            if self.is_skill_active:
                self.image = self.image_attack
            elif self.velocity.length() > 0 or self.is_dashing:
                self.image = self.image_walk
            else:
                self.image = self.image_idle
        
        # 바이킹 애니메이션 상태 업데이트
        elif self.character_key == 'viking':
            if self.is_skill_active:
                self.image = self.image_attack
            elif self.velocity.length() > 0 or self.is_dashing:
                self.image = self.image_walk
            else:
                self.image = self.image_idle

        # 마법사 애니메이션 상태 업데이트
        elif self.character_key == 'wizard':
            if self.is_skill_active:
                self.image = self.image_attack
            elif self.velocity.length() > 0 or self.is_dashing:
                self.image = self.image_walk
            else:
                self.image = self.image_idle

        self.rect.center = self.pos

    def draw(self, surface):
        surface.blit(self.image, self.rect)
