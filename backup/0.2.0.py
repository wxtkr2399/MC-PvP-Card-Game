# 兼容Python 3.11之前版本的Self类型注解
from __future__ import annotations
import json
import random
from queues_for_MP2 import RepeatQueue
import os

from logger import logger, log_clear

VERSION = "0.2.0"

ALLOW_COMMAND = True
EXIT_ON_ALL_HUMAN_DEAD = True
WAIT_FOR_AI_THINKING = True

if WAIT_FOR_AI_THINKING:
    import time

messages = {}

# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

language = "en_us"
lang_data: dict[str, str] = {}
def set_language(language_: str) -> None:
    """设置语言
    
    Args:
        language_: 语言代码
    """
    global language, lang_data
    language = language_

    try:
        # 构建语言文件的绝对路径
        lang_path = os.path.join(script_dir, "lang", f"{language}.json")
        with open(lang_path, "r", encoding="utf-8") as f:
            lang_data = json.load(f)
            msg = lang("message", "Successfully loaded language data")
            logger.debug(msg)
    except Exception as e:
        error_msg = lang("message", "Failed to load language data") + f": {str(e)}"
        logger.error(error_msg)
        lang_data = {}

    print()


name_path = os.path.join(script_dir, "name.txt")
with open(name_path, "r") as file:
    names = file.readlines()

def lang(type: str, key: str, *args, **kwargs) -> str:
    """获取本地化字符串
    
    Args:
        type: 本地化类型
        key: 本地化键名
        *args: 位置参数
        **kwargs: 命名参数
        
    Returns:
        本地化字符串
    """
    try:
        text = lang_data.get(type, {}).get(key, key)
    except:
        text = key

    # 如果有参数，则进行格式化
    if args or kwargs:
        try:
            return text.format(*args, **kwargs)
        except (KeyError, IndexError) as e:
            # 如果格式化失败，返回原始文本
            # print(f"Warning: Failed to format string '{text}' with args {args} and kwargs {kwargs}")
            return text
    return text

DAMAGE_PHYSICAL = "physical"
DAMAGE_EXPLOSIVE = "explosive"
DAMAGE_MAGICAL = "magical"
DAMAGE_COMMAND = "command"
DAMAGE_NONE = "none"


chosen_names = []

class Card:
    """表示游戏中的卡牌，包含卡牌名称和使用效果
    
    Attributes:
        name: 卡牌的本地化键名
    """
    def __init__(self, name: str) -> None:
        """初始化卡牌
        
        Args:
            name: 卡牌名称
            
        Raises:
            TypeError: 如果名称不是字符串
            ValueError: 如果名称以"/"开头且不允许命令
        """
        if not isinstance(name, str):
            raise TypeError("Card name must be a string")
        if not ALLOW_COMMAND and name[0] == "/":
            raise ValueError("Command are not allowed")
        name = name.strip()
            
        self.name: str = name

    def __str__(self) -> str:
        """返回卡牌的本地化名称
        
        Returns:
            卡牌的本地化名称
        """
        return lang("card", self.name)

    def __eq__(self, other: object) -> bool:
        """比较两张卡牌是否相同
        
        Args:
            other: 要比较的对象
            
        Returns:
            bool: 如果other是Card且名称相同返回True，否则False
        """
        if not isinstance(other, Card):
            return False
        return self.name == other.name
    
    def __hash__(self) -> int:
        """返回卡牌的哈希值
        
        Returns:
            卡牌名称的哈希值
        """
        return hash(self.name)

    def usage(self) -> tuple[int, str]:
        """获取卡牌的使用效果
        
        Returns:
            tuple: (伤害值, 伤害类型)
                  伤害值为0表示无伤害效果，类型为DAMAGE_NONE
        """
        weapon_damage = {
            "Wooden": 1,
            "Iron": 2,
            "Diamond": 3,
            "Netherite": 4
        }
        
        if self.name.endswith("Sword"):
            quality = self.name[:-5].strip()
            return (weapon_damage[quality], DAMAGE_PHYSICAL)
        if self.name.endswith("Axe"):
            quality = self.name[:-3].strip()
            return (weapon_damage[quality], DAMAGE_PHYSICAL)
        if self.name == "TNT":
            return (3, DAMAGE_EXPLOSIVE)
        if self.name == "Potion of Immediate Harm":
            return (2, DAMAGE_MAGICAL)
        if self.name == "/kill":
            if ALLOW_COMMAND:
                return (2**64, DAMAGE_COMMAND)

        return (0, DAMAGE_NONE)
    
    def need_target(self) -> bool:
        """判断卡牌是否需要目标
        
        Returns:
            bool: 如果需要目标返回True，否则False
        """
        return (self.name.endswith("Sword") or 
                self.name.endswith("Axe") or 
                self.name == "TNT")

def defendable(defence: str | None, damage_type: str) -> bool:
    """判断防御是否有效
    
    Args:
        defence: 防御装备名称
        damage_type: 伤害类型
        
    Returns:
        bool: 如果防御有效返回True，否则False
    """
    if not defence or damage_type == DAMAGE_COMMAND:
        return False
    if defence == "Shield":
        return damage_type not in (DAMAGE_MAGICAL, DAMAGE_EXPLOSIVE)
    return False

class Damage:  
    """表示游戏中的伤害信息
    
    Attributes:
        damage (int): 伤害值
        type (str): 伤害类型(physical/explosive/magical等)
        item (str): 造成伤害的物品名称
    """
    def __init__(self, damage: int, type: str, item: str) -> None:
        """初始化伤害信息
        
        Args:
            damage: 伤害值
            type: 伤害类型
            item: 造成伤害的物品名称
        """
        self.damage: int = damage
        self.type: str = type
        self.item: str = item

class Health:
    """管理玩家的生命值和防御状态
    
    Attributes:
        health (int): 当前生命值
        defence (str | None): 当前防御装备
        defence_times (int): 防御剩余次数
        parent_class (Player): 所属玩家对象
    """
    def __init__(self, health: int, player: "Player") -> None:
        """初始化生命值
        
        Args:
            health: 初始生命值
            player: 所属玩家对象
        """
        self.health: int = health
        self.defence: str | None = None
        self.defence_times: int = 0
        self.parent_class: Player = player

    def __str__(self) -> str:
        """返回生命值的字符串表示
        
        Returns:
            格式为"{health} HP"的字符串
        """
        return f"{self.health} HP"

    def __isub__(self, damage: Damage) -> "Health":
        """处理伤害计算(使用-=运算符)
        
        Args:
            damage: 受到的伤害信息
            
        Returns:
            self: 允许链式操作
            
        Note:
            会根据防御状态和伤害类型决定是否减免伤害
        """
        if not isinstance(damage, Damage):
            raise TypeError(f"Damage must be a Damage object, not {type(damage)}")

        if damage.damage <= 0:
            raise ValueError("Damage value must be positive")

        if self._handle_defense(damage):
            logger.debug(f"{self.parent_class.name}'s defense blocked {damage.item} damage")
            return self
            
        # 应用伤害
        self._apply_damage(damage)

        # 处理防御装备破坏
        self._check_defense_break(damage)
        self._check_bed_destoryed(damage)
        
        if self.health <= 0:
            self._handle_death()
            
        return self

    def _apply_damage(self, damage: Damage) -> None:
        """应用伤害到生命值
        
        Args:
            damage: 伤害信息
        """
        self.health -= damage.damage
        logger.debug(f"{self.parent_class.name} took {damage.damage} {damage.type} damage from {damage.item}, now has {self.health} HP")

    def _handle_death(self) -> None:
        """处理玩家死亡逻辑"""
        if self.parent_class.totem_of_undying:
            return
            
        self.parent_class.effects.clear()
        self.parent_class.cards.clear()
        global messages
        
        if not self.parent_class.bedded:
            death_msg = lang("message", "{} is dead", self.parent_class.name)
            logger.debug(death_msg)
            messages["death"] = death_msg
        else:
            self.health = 5
            self.parent_class.bedded = False
            self.parent_class.bed_defence = []
            revive_msg = lang("message", "{} relived with a bed", self.parent_class.name)
            logger.debug(revive_msg)
            messages["death"] = revive_msg

    def __iadd__(self, value: int) -> "Health":
        """处理生命值增加(使用+=运算符)
        
        Args:
            value: 增加的生命值
            
        Returns:
            self: 允许链式操作
        """

        if value <= 0:
            raise ValueError("Health value must be positive")

        health_boost_level = 0

        try:
            for effect in self.parent_class.effects:
                if effect.name == "health boost":
                    health_boost_level = max(health_boost_level, effect.level)
        except AttributeError:
            pass

        old_health = self.health
        self.health += value
        if self.health > 5 + health_boost_level:
            self.health = 5 + health_boost_level
        logger.debug(f"{self.parent_class.name} healed {self.health - old_health} HP, now has {self.health} HP")
        return self
        
    def _handle_defense(self, damage: Damage) -> bool:
        """处理防御逻辑
        
        Args:
            damage: 伤害信息
            
        Returns:
            bool: 如果伤害被防御返回True，否则False
        """
        if defendable(self.defence, damage.type) and self.defence_times > 0:
            self.defence_times -= 1
            if self.defence_times == 0:
                self.defence = None
                logger.debug(f"{self.parent_class.name}'s defense is broken")
            return True
        return False
        
    def _check_defense_break(self, damage: Damage) -> None:
        """检查防御装备是否被破坏
        
        Args:
            damage: 伤害信息
        """
        if self.defence == "Shield":
            if damage.item.endswith("Axe") or damage.type == DAMAGE_EXPLOSIVE:
                self.defence_times = 0
                self.defence = None
                global messages
                break_msg = lang("message", "{}'s shield is broken", self.parent_class.name)
                logger.debug(break_msg)
                messages["defence_break"] = break_msg

    def _check_bed_destoryed(self, damage: Damage) -> None:
        """检查床是否被破坏
        
        Args:
            damage: 伤害信息
        """
        if self.parent_class.bedded and damage.type in (DAMAGE_EXPLOSIVE):
            self.parent_class.bedded = False
            global messages
            bed_msg = lang("message", "{}'s bed is destoryed", self.parent_class.name)
            logger.debug(bed_msg)
            messages["bed_destoryed"] = bed_msg
    
class Effect:
    """表示游戏中的效果
    
    Attributes:
        name (str): 效果名称
        duration (int): 持续时间
    """
    def __init__(self, name: str, duration: int, level: int, parent_class: "Player") -> None:
        """初始化效果
        
        Args:
            name: 效果名称
            duration: 持续时间
            parent_class: 所属玩家对象
        """
        self.name: str = name.strip().lower()
        self.duration: int = duration
        self.parent_class: Player = parent_class
        self.level: int = level
        logger.debug(f"Effect '{self.name}' (level {level}) applied to {parent_class.name} for {duration} turns")
    
    def effect(self) -> None:
        """应用效果并减少持续时间
        
        Raises:
            ValueError: 如果效果名称无效
        """
        if self.name == "healing":
            self.parent_class.health += self.level
            logger.debug(f"Healing effect on {self.parent_class.name}: +{self.level} HP")
        elif self.name == "power":
            self.parent_class.power = self.level
            logger.debug(f"Power effect on {self.parent_class.name}: +{self.level} attack")
        elif self.name == "immediate_harm":
            self.parent_class.health -= Damage(self.level, DAMAGE_MAGICAL, "Potion of Immediate Harm")
            logger.debug(f"Immediate harm effect on {self.parent_class.name}: -{self.level} HP")
        elif self.name in ("health boost", ):
            logger.debug(f"Health boost effect active on {self.parent_class.name} (level {self.level})")
        else:
            raise ValueError(f"Unknown effect: {self.name}")

        self.duration -= 1
        if self.duration <= 0:
            try:
                self.parent_class.effects.remove(self)
                logger.debug(f"Effect '{self.name}' expired on {self.parent_class.name}")
            except ValueError:
                pass

        

class Player:
    """表示游戏玩家，包含玩家状态和卡牌操作
    
    Attributes:
        name (str): 玩家名称
        health (Health): 玩家生命值状态
        cards (list[Card]): 玩家持有的卡牌列表
        using (Card | None): 当前正在使用的卡牌
    """
    def __init__(self, name: str | None = None, AI_level: int = 0) -> None:
        """初始化玩家
        
        Args:
            name: 玩家名称
        """
        if name == None or name == "":
            name = random.choice(names).strip()
            while name in chosen_names:
                name = random.choice(names).strip()
            chosen_names.append(name)
        self.name: str = name
        self.health: Health = Health(5, self)
        self.cards: list[Card] = []
        self.using: Card | None = None
        self.effects: list[Effect] = []
        self.power: int = 0  # 增加玩家的攻击力
        self.AI_level: int = AI_level
        self.game: "Game" | None = None
        self.bedded: bool = False
        self.bed_defence: list[Damage] = []
        self.totem_of_undying: bool = False
        logger.debug(f"Player \"{self.name}\" created (AI level: {AI_level})")

    def __str__(self) -> str:        
        """返回玩家信息的字符串表示
        
        Returns:
            玩家信息（字符串）
        """
        return lang("message", "{name} ({health}, Cards: {cards}, Effects: {effects})", name=self.name, health=self.health, cards=", ".join([f"{i}: {card}" for i, card in enumerate(self.list_cards(), 1)]), effects=self.effects)
    
    def after_turn(self) -> None:        
        """处理玩家的每回合结束逻辑"""
        self.power = 0
        logger.debug(f"{self.name} processing after-turn effects")
        for effect in self.effects:
            effect.effect()


    def add_card(self, *card: Card) -> None:
        """添加卡牌到玩家手牌
        
        Args:
            card: 要添加的卡牌对象

        """
        self.cards += card
        for c in card:
            logger.debug(f"{self.name} received card: {c.name}")

    def _use_card(self, card: Card, cheat: bool = False) -> None:
        """使用卡牌的内部实现
        
        Args:
            card: 要使用的卡牌
            cheat: 是否允许作弊
        """
        if self.using:
            self.cards.append(self.using)
            logger.debug(f"{self.name} put back previous card: {self.using.name}")
            self.using = None
            
        if card in self.cards or cheat and ALLOW_COMMAND:
            if card in self.cards:
                self.cards.remove(card)
            self.using = card
            logger.debug(f"{self.name} selected card: {self.using.name}")
            
            # 处理不需要目标的卡牌
            if self.using.name in ("Shield", "Bed") or self.using.name.endswith("Apple"):
                self._handle_self_use_card()
            elif self.using.name.startswith("Potion of"):
                self._handle_potion_use()

    def _handle_self_use_card(self) -> None:
        """处理对自身使用的卡牌"""
        if self.using.name == "Shield":
            self.health.defence = self.using.name
            self.health.defence_times = 3
            logger.debug(f"{self.name} equipped Shield (3 defenses)")
        elif self.using.name == "Bed":
            self.bedded = True
            logger.debug(f"{self.name} placed a bed")
        elif self.using.name == "Apple":
            self.health += 1
        elif self.using.name == "Golden Apple":
            self.effects.append(Effect("Healing", 1, 1, self))
            self.effects.append(Effect("Health Boost", 3, 1, self))
            self.health += 1
        elif self.using.name == "Enchanted Golden Apple":
            self.effects.append(Effect("Healing", 2, 2, self))
            self.effects.append(Effect("Health Boost", 5, 2, self))
            self.health += 3

    def _handle_potion_use(self) -> None:
        """处理药水使用"""
        if self.using.name in ("Potion of Healing", "Potion of Health Boost"):
            # 检查是否已有相同效果
            effect_name = self.using.name[9:].strip().lower()
            existing_effect = next((e for e in self.effects if e.name == effect_name), None)
            if existing_effect:
                existing_effect.duration += 2  # 延长持续时间
                logger.debug(f"{self.name} extended effect {effect_name} duration by 2 turns")
            else:
                self.effects.append(Effect(effect_name, 2, 1, self))

    def _attack_player(self, target: "Player") -> None:
        """攻击其他玩家的内部实现
        
        Args:
            target: 目标玩家
        """
        if self.using is not None:
            logger.debug(f"{self.name} attacking {target.name} with {self.using.name}")
            target.be_attacked(self.using, self)
            self.using = None
        else:
            error_msg = f"{self.name} is not using any card"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def __call__(self, card_or_target: Card | "Player" | None = None, cheat: bool = False) -> None:
        """特殊方法，允许使用卡牌或攻击其他玩家
        
        根据参数类型决定行为：
        - 如果是Card: 使用该卡牌(装备或治疗)
        - 如果是Player: 使用当前卡牌攻击该玩家
        
        Args:
            card_or_target: 卡牌对象或玩家对象(若为None则表示不使用卡牌)
            
        Raises:
            ValueError: 如果卡牌不在手牌中或没有使用中的卡牌
            TypeError: 如果参数类型无效
        """
        if isinstance(card_or_target, Card):
            self._use_card(card_or_target, cheat)
        elif isinstance(card_or_target, Player):
            self._attack_player(card_or_target)
        elif card_or_target is None:
            logger.debug(f"{self.name} passed turn")
        else:
            error_msg = f"Invalid argument type: {type(card_or_target)}"
            logger.error(error_msg)
            raise TypeError(error_msg)
        
    def be_attacked(self, card: Card, attacker: "Player") -> None:
        """处理被攻击逻辑
        
        Args:
            card: 用于攻击的卡牌对象
            attacker: 攻击者对象
        """
        damage_value, damage_type = card.usage()
        if damage_value > 0:
            # 增加攻击力加成
            if hasattr(attacker, "power"):
                damage_value += attacker.power
            self.health -= Damage(damage_value, damage_type, card.name)

    def list_cards(self) -> list[Card]:
        return list(self.cards)
    
    def _ai_level_1_action(self, other_players: list["Player"]) -> None:
        """AI等级1的行为：随机策略
        
        Args:
            other_players: 其他玩家列表
        """
        card = random.choice(self.cards)
        self(card)
        if card.need_target() and other_players:
            target = random.choice(other_players)
            self(target)
            action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=card.name, target=target.name)
            logger.debug(action_msg)
            print(action_msg)
        else:
            action_msg = lang("message", "{player} used {card}", player=self.name, card=card.name)
            logger.debug(action_msg)
            print(action_msg)

    def _get_healing_cards(self) -> list[Card]:
        """获取治疗类卡牌"""
        return [c for c in self.cards if c.name in ("Potion of Healing", "Apple", "Golden Apple", "Enchanted Golden Apple")]
    
    def _get_attack_cards(self) -> list[Card]:
        """获取攻击类卡牌"""
        return [c for c in self.cards if c.need_target()]
    
    def _get_non_attack_cards(self) -> list[Card]:
        """获取非攻击类卡牌"""
        return [c for c in self.cards if not c.need_target()]
    
    def _use_healing_if_needed(self, threshold: int = 4) -> bool:
        """如果需要治疗则使用治疗卡牌"""
        if self.health.health < threshold:
            healing_cards = self._get_healing_cards()
            if healing_cards:
                card = random.choice(healing_cards)
                self(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=card.name)
                logger.debug(action_msg)
                print(action_msg)
                return True
        return False
    
    def _use_best_attack_card(self, other_players: list["Player"]) -> bool:
        """使用最佳攻击卡牌攻击最脆弱的敌人"""
        attack_cards = self._get_attack_cards()
        if attack_cards and other_players:
            attack_cards.sort(key=lambda c: c.usage()[0], reverse=True)
            card = attack_cards[0]
            self(card)
            other_players.sort(key=lambda p: p.health.health)
            target = other_players[0]
            self(target)
            action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=card.name, target=target.name)
            logger.debug(action_msg)
            print(action_msg)
            return True
        return False
    
    def _use_random_non_attack_card(self) -> bool:
        """随机使用非攻击卡牌"""
        non_attack_cards = self._get_non_attack_cards()
        if non_attack_cards:
            card = random.choice(non_attack_cards)
            self(card)
            action_msg = lang("message", "{player} used {card}", player=self.name, card=card.name)
            logger.debug(action_msg)
            print(action_msg)
            return True
        return False

    def _ai_level_2_action(self, other_players: list["Player"]) -> None:
        """AI等级2的行为：中级策略"""
        # 尝试治疗
        if self._use_healing_if_needed(4):
            return
            
        # 50%概率优先攻击
        if random.random() < 0.5 and self._use_best_attack_card(other_players):
            return
            
        # 最后使用非攻击卡牌
        if self._use_random_non_attack_card():
            return
    
    def _ai_level_3_action(self, other_players: list["Player"]) -> None:
        """AI等级3的行为：高级策略"""
        # 尝试各种策略，按优先级顺序
        strategies = [
            self._use_emergency_healing,
            self._use_defense,
            self._use_power_potions,
            self._use_normal_healing,
            lambda: self._use_attack_with_kill_priority(other_players),
            self._use_random_card
        ]
        
        for strategy in strategies:
            if strategy():
                return
    
    def _use_emergency_healing(self) -> bool:
        """使用紧急治疗"""
        if self.health.health <= 3:
            # 优先使用附魔金苹果
            enchanted_golden_apples = [c for c in self.cards if c.name == "Enchanted Golden Apple"]
            if enchanted_golden_apples:
                card = random.choice(enchanted_golden_apples)
                self(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=card.name)
                logger.debug(action_msg)
                print(action_msg)
                return True
                
            # 其次使用普通金苹果
            golden_apples = [c for c in self.cards if c.name == "Golden Apple"]
            if golden_apples:
                card = random.choice(golden_apples)
                self(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=card.name)
                logger.debug(action_msg)
                print(action_msg)
                return True
        return False
    
    def _use_defense(self) -> bool:
        """使用防御装备"""
        if self.health.defence is None:
            enchanted_shields = [c for c in self.cards if c.name == "Enchanted Shield"]
            if enchanted_shields:
                card = random.choice(enchanted_shields)
                self(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=card.name)
                logger.debug(action_msg)
                print(action_msg)
                return True
        return False
    
    def _use_power_potions(self) -> bool:
        """使用力量药水"""
        power_potions = [c for c in self.cards if c.name == "Potion of Power"]
        if power_potions:
            card = random.choice(power_potions)
            self(card)
            action_msg = lang("message", "{player} used {card}", player=self.name, card=card.name)
            logger.debug(action_msg)
            print(action_msg)
            return True
        return False
    
    def _use_normal_healing(self) -> bool:
        """使用普通治疗"""
        if self.health.health < 5:
            apples = [c for c in self.cards if c.name == "Apple"]
            if apples:
                card = random.choice(apples)
                self(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=card.name)
                logger.debug(action_msg)
                print(action_msg)
                return True
        return False
    
    def _use_attack_with_kill_priority(self, other_players: list["Player"]) -> bool:
        """优先使用能消灭敌人的攻击"""
        attack_cards = self._get_attack_cards()
        if attack_cards and other_players:
            # 按伤害值降序排序
            attack_cards.sort(key=lambda c: c.usage()[0], reverse=True)
            
            # 寻找能消灭敌人的卡牌
            for card in attack_cards:
                damage = card.usage()[0]
                for target in other_players:
                    if target.health.health <= damage:
                        self(card)
                        self(target)
                        action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=card.name, target=target.name)
                        logger.debug(action_msg)
                        print(action_msg)
                        return True
            
            # 没有能消灭的敌人，使用最高伤害攻击最低生命
            card = attack_cards[0]
            other_players.sort(key=lambda p: p.health.health)
            target = other_players[0]
            self(card)
            self(target)
            action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=card.name, target=target.name)
            logger.debug(action_msg)
            print(action_msg)
            return True
        return False
    
    def _use_random_card(self) -> bool:
        """随机使用一张卡牌"""
        if self.cards:
            card = random.choice(self.cards)
            self(card)
            other_players = [p for p in self.game.players_in_order if p != self and p.health.health > 0]
            
            # 处理需要目标的卡牌
            if card.need_target() and other_players:
                target = random.choice(other_players)
                self(target)
                action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=card.name, target=target.name)
                logger.debug(action_msg)
                print(action_msg)
            elif card.need_target():  # 无可用目标时取消使用
                logger.debug(f"{self.name} canceled card usage (no target)")
                print(lang("message", "{player} did nothing", player=self.name))
                return False
            return True
        return False

    def AI_action(self) -> None:
        """AI玩家的行动，由AI_level决定
        
        AI_level为0时，代表是人类玩家
                为1时，随机出牌
                为2时，优先使用非攻击卡牌，然后使用最高伤害攻击最低生命玩家
                为3时，根据状态智能决策（治疗/防御/增益/攻击）
        """
        if self.AI_level == 0:
            return

        if WAIT_FOR_AI_THINKING:
            time.sleep(random.uniform(0.5, 2.5))

        other_players = [p for p in self.game.players_in_order if p != self and p.health.health > 0]

        if not other_players or not self.cards:
            logger.debug(f"{self.name} has no valid action")
            return
            
        # 使用策略模式处理不同AI等级
        strategy_handlers = {
            1: self._ai_level_1_action,
            2: self._ai_level_2_action,
            3: self._ai_level_3_action
        }
        
        handler = strategy_handlers.get(self.AI_level)
        if handler:
            handler(other_players)
        else:
            logger.debug(f"{self.name} did nothing")
            print(lang("message", "{player} did nothing", player=self.name))

    def info(self) -> str:
        """返回玩家信息的字符串表示
        
        Returns:
            格式为"{player} ({health}, Cards: {cards}, Effects: {effects})"的字符串

        """
        return f"{self.name} ({self.health}, Cards: {", ".join([f"{i}: {card}" for i, card in enumerate(self.current_player.list_cards(), 1)])}, Effects: {self.effects})"

      
class CardPool:
    """管理卡牌池
    
    Attributes:
        cards (dict[Card, int]): 卡牌列表及其数量
    """

    default: dict[Card, int] = {
        Card("Wooden Sword"): 5,
        Card("Iron Sword"): 4, 
        Card("Diamond Sword"): 2, 
        Card("Netherite Sword"): 1, 
        Card("Wooden Axe"): 4, 
        Card("Iron Axe"): 3, 
        Card("Diamond Axe"): 2, 
        Card("Netherite Axe"): 1, 
        Card("TNT"): 3, 
        Card("Apple"): 4, 
        Card("Golden Apple"): 2,
        Card("Enchanted Golden Apple"): 1,
        Card("Potion of Healing"): 2,
        Card("Potion of Power"): 1,
        Card("Shield"): 3,
        Card("Bed"): 1,
        Card("Potion of Immediate Harm"): 2,
    }

    def __init__(self, cards: dict[Card, int] = default.copy()) -> None:
        """初始化卡牌池
        
        Args:
            cards: 卡牌列表及其数量
        """
        self.cards: dict[Card, int] = cards
        logger.debug("Card pool initialized")

    def reset(self) -> None:
        self.cards = CardPool.default.copy()
        logger.debug("Card pool reset to default")

    def add_card(self, card: Card, count: int = 1) -> None:
        """添加卡牌到卡牌池
        
        Args:
            card: 要添加的卡牌对象
            count: 要添加的数量，默认为1
        """
        if card in self.cards:
            self.cards[card] += count
        else:
            self.cards[card] = count
        logger.debug(f"Added {count}x {card.name} to card pool")

    def draw_card(self, amount: int = 1) -> list[Card]:
        """从卡牌池中随机抽取一张卡牌
        
        Returns:
            随机抽取的卡牌对象
        """
        chosen: list[Card] = []
        if len(self.cards) < amount:
            self.reset()
        for _ in range(amount):
            card, count = random.choice(list(self.cards.items()))
            if count > 1:
                self.cards[card] -= 1
            else:
                del self.cards[card]
            chosen.append(card)
        logger.debug(f"Drew card: {', '.join([c.name for c in chosen])}")
        return chosen

    def __str__(self) -> str:
        """返回卡牌池的字符串表示
        
        Returns:
            卡牌名称及数量的字符串
        """
        return ", ".join(f"{str(card)} x{count}" for card, count in self.cards.items())
    
    def __add__(self, other: CardPool) -> CardPool:
        """合并两个卡牌池
        
        Args:
            other: 要合并的卡牌池
        
        Returns:
            合并后的卡牌池
        """
        new_pool = CardPool()
        for card, count in self.cards.items():
            new_pool.add_card(card, count)
        for card, count in other.cards.items():
            new_pool.add_card(card, count)
        logger.debug("Merged two card pools")
        return new_pool

class Game:
    """游戏主类，负责管理游戏状态和流程"""
    
    def __init__(self, players: list[Player] | None = []) -> None:
        """
        初始化游戏
        
        Args:
            players: 参与游戏的玩家列表
        """
        self.players: RepeatQueue[Player] = RepeatQueue(players)
        self.current_player_index: int = 0
        self.is_game_over: bool = False
        self.turn_count: int = 0
        self._current_turn_players: set[Player] = set()
        self.started: bool = False
        self.winner: Player | None = None
        self.card_pool: CardPool = CardPool()
        self.players_in_order: list[Player] = []
        logger.debug("Game initialized")

    def add_player(self, *players: Player) -> None:
        """添加玩家到游戏
        
        Args:
            *players: 一个或多个玩家对象
        """
        for player in players:
            self.players.put(player)
            self.players_in_order.append(player)
            player.game = self
            logger.debug(f"Added player: {player.name}")

    def start_game(self) -> None:
        """开始游戏，初始化玩家手牌和游戏状态"""
        if len(self.players) < 2:
            logger.error("Not enough players to start game")
            print("Not enough players")
            return

        # 为每个玩家发初始卡牌
        for player in self.players:
            player.add_card(*self.card_pool.draw_card(5))
        self.is_game_over = False
        self.turn_count = 1
        logger.debug("Game started")
        
    @property
    def current_player(self) -> Player:
        """获取当前玩家
        
        Returns:
            当前回合的玩家
        """
        return self.players[0]
        
    def next_turn(self) -> None:
        """切换到下一回合"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn_count += 1
        self.check_game_over()
        logger.debug(f"Turn advanced to {self.turn_count}")
        
    def check_game_over(self) -> bool:
        """检查游戏是否结束
        
        Returns:
            bool: 如果游戏结束返回True，否则False
        """
        active_players = [p for p in self.players if p.health.health > 0]
        if len(active_players) <= 1:
            self.is_game_over = True
            logger.debug("Game over condition met")
        return self.is_game_over


    def after_turn(self) -> None:
        """处理所有玩家的每回合结束逻辑
        
        Args:
            player_queue: 玩家队列
        """
        if not self.players:
            logger.error("No players found for after_turn processing")
            print("No players found!")
            return

        logger.debug("Processing after-turn effects for all players")
        for player in self.players:
            player.after_turn()

    def _setup_game(self) -> None:
        """初始化游戏设置"""
        start_msg = lang("message", "Game started!")
        logger.debug(start_msg)
        print(start_msg)
        
        card_pool_msg = lang("message", "Card pool: {}", str(self.card_pool))
        logger.debug(card_pool_msg)
        print(card_pool_msg)
        
        players_msg = lang("message", "Players: {}", ", ".join(player.name for player in self.players))
        logger.debug(players_msg)
        print(players_msg)
        print()
        # 为每个玩家生成本地化的字符串表示
        for player in self.players:
            player.add_card(*self.card_pool.draw_card(5))
            
    def _display_player_status(self, player: Player) -> None:
        """显示玩家状态
        
        Args:
            player: 要显示状态的玩家
        """
        health_msg = lang("message", "Health: {} HP", player.health.health)
        logger.debug(health_msg)
        print(health_msg)
        
        if player.bedded:
            if player.bed_defence:
                bed_msg = lang("message", "Bed state: be protected with {}", player.bed_defence[0])
                logger.debug(bed_msg)
                print(bed_msg)
            else:
                bed_msg = lang("message", "Bed state: Bedded")
                logger.debug(bed_msg)
                print(bed_msg)
        else:
            bed_msg = lang("message", "Bed state: Unbedded")
            logger.debug(bed_msg)
            print(bed_msg)

    def _handle_card_selection(self, player: Player) -> Card | None:
        """处理卡牌选择
        
        Args:
            player: 当前玩家
            
        Returns:
            选择的卡牌或None
        """
        if not player.cards:
            no_cards_msg = lang("message", "No cards left in {player}'s hand", player=player.name)
            logger.debug(no_cards_msg)
            print(no_cards_msg)
            player.add_card(*self.card_pool.draw_card(5))
            return None
            
        # 本地化输入提示
        card_index = input(lang("message", "Enter card index to use (0 to draw 2 cards): "))
        if card_index == "0":
            logger.debug(f"{player.name} drew 2 cards")
            drawn_cards = self.card_pool.draw_card(2)
            player.add_card(*drawn_cards)
            # 本地化抽牌消息
            draw_msg = lang("message", "{player} drew {count} cards: {cards}", player=player.name, count=len(drawn_cards), cards=", ".join(str(card) for card in drawn_cards))
            logger.debug(draw_msg)
            print(draw_msg)
            print()
            return None
            
        try:
            card = player.list_cards()[int(card_index) - 1]
            logger.debug(f"{player.name} selected card: {card.name}")
            return card
        except:
            error_msg = lang("message", "Invalid card index")
            logger.error(error_msg)
            print(error_msg)
            return None

    def _handle_target_selection(self, player: Player, card: Card) -> Player | None:
        """处理目标选择
        
        Args:
            player: 当前玩家
            card: 使用的卡牌
            
        Returns:
            选择的目标玩家或None
        """
        targets = [p for p in self.players_in_order if p != player and p.health.health > 0]
        # 本地化目标选择提示
        targets_list = [f"{i}: {p.name}" for i, p in enumerate(targets, 1)]
        targets_msg = lang("message", "Players to be target: {}", ", ".join(targets_list))
        logger.debug(targets_msg)
        print(targets_msg)
        target_index = input(lang("message", "Enter target player index: "))
        try:
            target_player = targets[int(target_index)-1]
            # 本地化攻击消息
            attack_msg = lang("message", "{player} attacks {target} with {card}", 
                player=player.name, target=target_player.name, card=str(card))
            logger.debug(attack_msg)
            print(attack_msg)
            return target_player
        except Exception as e:
            error_msg = lang("message", "Invalid target player index")
            logger.error(error_msg)
            print(error_msg)
            return None

    def _handle_player_turn(self, player: Player) -> None:
        """处理单个玩家回合
        
        Args:
            player: 当前回合的玩家
        """
        turn_msg = lang("message", "{player}'s turn", player=player.name)
        logger.debug(turn_msg)
        print(turn_msg)
        
        if player.AI_level:
            self._display_player_status(player)
            print("...")

            global messages

            messages = {}
            messages.setdefault("death", "")
            messages.setdefault("defence_break", "")

            player.AI_action()

            if messages["defence_break"]:
                print(messages["defence_break"])

            if messages["death"]:
                print(messages["death"])

            print()
        else:
            self._handle_human_turn(player)

            
    def _handle_human_turn(self, player: Player) -> None:
        """处理人类玩家回合
        
        Args:
            player: 当前回合的人类玩家
        """
        self._display_player_status(player)
        
        # 本地化显示玩家手牌
        cards_list = [f"{i}: {card}" for i, card in enumerate(player.list_cards(), 1)]
        cards_msg = lang("message", "Cards: {}", ", ".join(cards_list))
        logger.debug(cards_msg)
        print(cards_msg)

        if player.AI_level:
            return

        # 处理卡牌选择
        card = self._handle_card_selection(player)
        if card is None:
            return
            
        player(card)

        if card.need_target():
            # 处理目标选择
            target = self._handle_target_selection(player, card)
            if target is None:
                return
            player(target)
        else:
            # 本地化使用卡牌消息
            card_use_msg = lang("message", "{player} used {card}", player=player.name, card=str(card))
            logger.debug(card_use_msg)
            print(card_use_msg)

        print()
            
        player.using = None
        
    def _is_turn_finished(self) -> bool:
        """判断当前回合是否结束
        
        当所有存活玩家都行动过一次后，回合结束
        
        Returns:
            bool: 如果回合结束返回True，否则False
        """
        current_player = self.players.front()
        self._current_turn_players.add(current_player)
        
        # 检查所有存活玩家是否都已行动
        alive_players = [p for p in self.players if p.health.health > 0]
        if len(self._current_turn_players) == len(alive_players):
            self._current_turn_players.clear()
            return True
        return False
            
    def start(self) -> None:
        """开始并进行游戏"""
        logger.debug("Starting game")
        self.started = True
        self._setup_game()
        
        while len(self.players) > 1:
            player = self.players.peek()
            if player.health.health <= 0:
                self.players.remove(player)
                continue
                
            self._handle_player_turn(player)
            
            if self._is_turn_finished():
                self.after_turn()

            if EXIT_ON_ALL_HUMAN_DEAD and self._check_human_dead():
                break
        else:
            game_over_msg = lang("message", "Game over!")
            logger.debug(game_over_msg)
            print(game_over_msg)

            winner_msg = lang("message", "{} wins!", self.players.peek().name)
            logger.debug(winner_msg)
            print(winner_msg)
            self.winner = self.players.peek()

            return

        game_over_msg = lang("message", "Game exited for no human alive!")
        logger.debug(game_over_msg)
        print(game_over_msg)
    
    def _check_human_dead(self) -> bool:
        """检查是否所有人类玩家都死亡
        
        Returns:
            bool: 如果所有人类玩家都死亡返回True，否则False
        """
        human_players = [p for p in self.players if not p.AI_level]
        return all(p.health.health <= 0 for p in human_players)

def main():
    log_clear()

    # 初始化日志
    logger.debug("Game starting")
    set_language("zh_cn")

    game = Game()
    game.add_player(Player("You"), *[Player("", 3) for _ in range(3)])

    for _ in range(0):
        game.card_pool += game.card_pool

    game.start()
    logger.debug("Game ended")

def test():
    player1 = Player("player1")
    player2 = Player("player2")
    
    player1.bedded = True

    kill = Card("/kill")
    print(kill.usage())

    player2.add_card(kill)

    player2(kill)
    player2(player1)

    print(player1.health.health)

if __name__ == "__main__":
    main()