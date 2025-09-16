# 兼容Python 3.11之前版本的Self类型注解
from __future__ import annotations
import time
import json
import random
from typing import Callable
from MP2_dataType import RepeatQueue, Stack
import os

from logger import logger, log_clear

__all__ = [
    "VERSION",
    "ALLOW_COMMAND",
    "EXIT_ON_ALL_HUMAN_DEAD",
    "WAIT_FOR_AI_THINKING",
    "DEBUG",
    "set_language",
    "Card",
    "Player",
    "Game",
]

VERSION = "0.5.0"

# 游戏设置(bool)
ALLOW_COMMAND = "allow_command"
EXIT_ON_ALL_HUMAN_DEAD = "exit_on_all_human_dead"
WAIT_FOR_AI_THINKING = "wait_for_ai_thinking"
DEBUG = "debug"

# 游戏设置(int)
START_HEALTH = "start_health"
MAX_HEALTH = "max_health"

messages = {}

DAMAGE_PHYSICAL = "physical"
DAMAGE_EXPLOSIVE = "explosive"
DAMAGE_MAGICAL = "magical"
DAMAGE_COMMAND = "command"
DAMAGE_NONE = "none"

DESTROY_EXPLOSIVE = "explosive"
DESTROY_AXE = (DEFENCE_STONE := "stone")
DESTROY_PICKAXE = (DEFENCE_WOOD := "wood")
DESTROY_NONE = (DEFENCE_NONE := "none")


# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

language = "en_us"
lang_data: dict[str, str] = {}

def set_language(language_: str, part: list[str] = [], reload: bool = False) -> None:
    """设置语言
    
    Args:
        language_: 语言代码
        part: 语言部分
        reload: 是否重新加载语言数据
    """
    global language, lang_data
    language = language_

    try:
        # 构建语言文件的绝对路径
        lang_path = os.path.join(script_dir, "lang", f"{language}.json")
        with open(lang_path, "r", encoding="utf-8") as f:
            loading_ = json.load(f)
            if part:
                for p in part:
                    loading = loading_.get(p, {})
            else:
                loading = loading_
            if reload:
                lang_data = loading
            else:
                lang_data.update(loading)
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
            logger.warning(f"Warning: Failed to format string '{text}' with args {args} and kwargs {kwargs}")
            return text
    return text


chosen_names = []

class Card:
    """表示游戏中的卡牌，包含卡牌名称和使用效果
    
    Attributes:
        name: 卡牌的本地化键名
    """
    def __init__(self, name: str, game: Game = None) -> None:
        """初始化卡牌
        
        Args:
            name: 卡牌名称
            
        Raises:
            TypeError: 如果名称不是字符串
            ValueError: 如果名称以"/"开头且不允许命令
        """
        if not isinstance(name, str):
            raise TypeError("Card name must be a string")

        # 处理game为None的情况
        if game is None:
            from main import Game  # 延迟导入
            game = Game()

        if name[0] == "/" and not game.get_setting(ALLOW_COMMAND):
            raise ValueError("Command are not allowed")

        self.game = game 
        self.name: str = name.strip()

    def __str__(self) -> str:
        """返回卡牌的本地化名称
        
        Returns:
            卡牌的本地化名称
        """
        return lang("card", self.name)

    def __repr__(self) -> str:
        return f"Card(name={self.name})"

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
                  伤害值为-1表示秒杀，类型为DAMAGE_COMMAND
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
        if self.name.endswith("Pickaxe"):
            quality = self.name[:-7].strip()
            return (weapon_damage[quality] // 2, DAMAGE_PHYSICAL)
        if self.name[0] == "/" and self.game.get_setting(ALLOW_COMMAND):
            return {
                "/kill": (-1, DAMAGE_COMMAND),
            }.get(self.name, (0, DAMAGE_NONE))

        return {
            "TNT": (3, DAMAGE_EXPLOSIVE),
            "Potion of Instant Damage": (2, DAMAGE_MAGICAL),
            "Trident": (3, DAMAGE_PHYSICAL),
            "Damaged Trident": (1, DAMAGE_PHYSICAL),
            "TNT Minecart": (2, DAMAGE_EXPLOSIVE),
        }.get(self.name, (0, DAMAGE_NONE))

    def destroy_defense_type(self) -> tuple[str, int, bool]:
        """获取卡牌的破坏/防御类型
        
        Returns:
            tuple: (破坏/防御类型, 破坏(<0)/防御(>0)值, 是否可防御爆炸)
        """
        defence = {
            "Wooden Block": (DEFENCE_WOOD, 2),
            "Stone Block": (DEFENCE_STONE, 2),
            "Obsidian Block": (DEFENCE_STONE, 5, True),
            "Glass Block": (DEFENCE_NONE, 0, True),
        }.get(self.name, (DEFENCE_NONE, 0, False))
        if defence[1] > 0:
            if len(defence) == 2:
                return (*defence, False)
            return defence

        if self.usage()[1] == DAMAGE_EXPLOSIVE:
            return (DESTROY_EXPLOSIVE, -self.usage()[0])

        weapon_damage = {
            "Wooden": 1,
            "Iron": 2,
            "Diamond": 3,
            "Netherite": 4
        }

        if self.name.endswith("Axe"):
            quality = self.name[:-3].strip()
            return (DESTROY_AXE, -weapon_damage[quality])
        if self.name.endswith("Pickaxe"):
            quality = self.name[:-7].strip()
            return (DESTROY_PICKAXE, -weapon_damage[quality])
        return (DESTROY_NONE, 0)
    
    def need_target(self) -> bool:
        """判断卡牌是否需要目标
        
        Returns:
            bool: 如果需要目标返回True，否则False
        """
        return (self.name.endswith("Sword") or 
                self.name.endswith("Axe") or 
                self.name in ("Potion of Instant Damage", "TNT", "TNT Minecart", "Trident", "Damaged Trident"))

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
        return damage_type not in (DAMAGE_MAGICAL, )
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

def BedDefenceFromCard(card: Card, owner: "Player") -> "BedDefence":
    """从卡牌创建床防御装备
    
    Args:
        card: 用于创建防御装备的卡牌
        owner: 装备所属玩家
        
    Returns:
        BedDefence: 创建的床防御装备对象
    """
    return BedDefence(card.name, *card.destroy_defense_type(), owner)

class BedDefence:
    """表示游戏中的床防御装备
    
    Attributes:
        name (str): 装备名称
        defence (str): 防御类型
        times (int): 防御次数
        can_fend_explosive (bool): 是否可以防御爆炸
        parent_class (Player): 装备所属玩家
    """
    def __init__(self, name: str, defence: str, times: int = 1, can_fend_explosive: bool = False, parent_class: "Player" = None) -> None:
        """初始化床防御装备
        
        Args:
            name: 装备名称
            defence: 防御类型
            times: 防御次数
            can_fend_explosive: 是否可以防御爆炸
            parent_class: 装备所属玩家
        """
        if name.endswith(" Block"):
            self.name: str = name[:-6]
        else:
            self.name: str = name
        self.defence: str = defence
        self.times: int = times
        self.can_fend_explosive: bool = can_fend_explosive
        self.parent_class: "Player" = parent_class

    def can_be_destroyed(self, tool: Card) -> bool:
        """判断装备是否可以被工具破坏
        
        Args:
            tool: 用于破坏的工具卡牌
            
        Returns:
            bool: 如果装备可以被工具破坏返回True，否则False
        """
        if self.can_fend_explosive and tool.destroy_defense_type() == DESTROY_EXPLOSIVE:
            return True
        return tool.destroy_defense_type() == self.defence and self.times > 0


    def destroy_by(self, tool: Card) -> None:
        if self.can_be_destroyed(tool):
            self.times -= 1
            logger.debug(f"{self.name} destroyed by {tool.name}")
            if self.times <= 0:
                self.parent_class.bed_defence.pop()
                logger.debug(f"{self.name} destroyed")

        def __str__(self) -> str:
            return f"{self.name} (防御: {self.defence}, 次数: {self.times})"

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
        self.max_health: int = health
        self.defence: str | None = None
        self.defence_times: int = 0
        self.parent_class: Player = player

    def __str__(self) -> str:
        """返回生命值的字符串表示
        
        Returns:
            格式为"{health} HP"的字符串
        """
        return f"{self.health} HP"

    def __int__(self) -> int:
        """返回生命值的整数表示
        
        Returns:
            当前生命值
        """
        return self.health

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

        if damage.damage < 0 and damage.type != DAMAGE_COMMAND:
            raise ValueError("Damage value must be positive")

        if damage.type == DAMAGE_COMMAND and damage.damage == -1:
            self.health = 0
            return self

        if self._handle_defense(damage):
            logger.debug(f"{self.parent_class.name}'s defense blocked {damage.item} damage")
            return self
                       
        # 应用伤害
        self._apply_damage(damage)

        # 处理防御装备破坏
        self._check_defense_break(damage)
        if damage.type == DAMAGE_EXPLOSIVE:
            if self.parent_class.bed_defence.is_empty():
                self.parent_class.bedded = False
                self.parent_class.bed_defence = Stack()
            else:
                self.parent_class.bed_defence.peek().destroy_by(damage.item)

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
        self.parent_class.effects.clear()
        self.parent_class.cards.clear()

        global messages
        
        if not self.parent_class.bedded:
            death_msg = lang("message", "{} is dead", self.parent_class.name)
            logger.debug(death_msg)
            print(death_msg)
        else:
            self.health = 5
            self.parent_class.bedded = False
            self.parent_class.bed_defence = Stack()
            revive_msg = lang("message", "{} relived with a bed", self.parent_class.name)
            logger.debug(revive_msg)
            print(revive_msg)

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
        if self.health > self.max_health + health_boost_level:
            self.health = self.max_health + health_boost_level
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
        elif self.name == "instant damage":
            self.parent_class.health -= Damage(self.level, DAMAGE_MAGICAL, "Potion of Instant Damage")
            logger.debug(f"Instant Damage effect on {self.parent_class.name}: -{self.level} HP")
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
        using (Stack[Card]): 当前正在使用的卡牌
    """
    def __init__(self, name: str | None = None, AI_level: int = 0) -> None:
        """初始化玩家
        
        Args:
            name: 玩家名称

        Attributes:
            name (str): 玩家名称
            health (Health): 玩家生命值状态
            cards (list[Card]): 玩家持有的卡牌列表
            using (Stack[Card]): 当前正在使用的卡牌
            effects (list[Effect]): 玩家当前生效的效果列表
            power (int): 玩家当前攻击力
            AI_level (int): 玩家AI等级
            game (Game): 玩家所属游戏对象
            bedded (bool): 玩家是否有床
            bed_defence (Stack[BedDefence]): 玩家床的防御装备
            delay_attack_this_turn (list[tuple[Card, Player]]): 玩家这回合延迟攻击的卡牌列表
        """
        if name == None or name == "":
            name = random.choice(names).strip()
            while name in chosen_names:
                name = random.choice(names).strip()
            chosen_names.append(name)
        self.name: str = name
        self.health: Health = Health(5, self)
        self.cards: list[Card] = []
        self.using: Stack[Card] = Stack()
        self.effects: list[Effect] = []
        self.power: int = 0  # 增加玩家的攻击力
        if not 0 <= AI_level <= 3:
            raise ValueError("AI level must be between 0 and 3")
        self.AI_level: int = AI_level
        self.game: "Game" | None = None
        self.bedded: bool = False
        self.bed_defence: Stack[BedDefence] = Stack()
        self.delay_attack_this_turn: list[tuple[Card, Player]] = []
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
        if not self.using.is_empty():
            self.cards.append(self.using.peek())
            logger.debug(f"{self.name} put back previous card: {self.using.pop().name}")
            
        if card in self.cards or cheat:
            if card in self.cards and not cheat:
                self.cards.remove(card)
            self.using.push(card)
            logger.debug(f"{self.name} selected card: {self.using.peek().name}")
            
            # 处理不需要目标的卡牌
            if not card.need_target():
                if self.using.peek().name in ("Shield", "Bed") or self.using.peek().name.endswith("Apple"):
                    self._handle_self_use_card()
                elif self.using.peek().name.startswith("Potion of"):
                    self._handle_potion_use()
                
            try:
                if not cheat:  # 只有非作弊模式才放入弃牌堆
                    self.game.card_pool.put_back(self.using.pop())
            except:
                pass

    def _handle_self_use_card(self) -> None:
        """处理对自身使用的卡牌"""
        if self.using.peek().name == "Shield":
            self.health.defence = self.using.peek().name
            self.health.defence_times = 3
            logger.debug(f"{self.name} equipped Shield (3 defenses)")
        elif self.using.peek().name == "Bed":
            self.bedded = True
            logger.debug(f"{self.name} placed a bed")
        elif self.using.peek().name == "Apple":
            self.health += 1
        elif self.using.peek().name == "Golden Apple":
            self.effects.append(Effect("Healing", 1, 1, self))
            self.effects.append(Effect("Health Boost", 3, 1, self))
            self.health += 1
        elif self.using.peek().name == "Enchanted Golden Apple":
            self.effects.append(Effect("Healing", 2, 2, self))
            self.effects.append(Effect("Health Boost", 5, 2, self))
            self.health += 3
        
        logger.debug(f"{self.name} used card: {self.using.peek().name}")

    def _handle_potion_use(self) -> None:
        """处理药水使用"""
        if self.using.peek().name in ("Potion of Healing", "Potion of Health Boost"):
            # 检查是否已有相同效果
            effect_name = self.using.peek().name[9:].strip().lower()
            existing_effect = next((e for e in self.effects if e.name == effect_name), None)
            if existing_effect:
                existing_effect.duration += 2  # 延长持续时间
                logger.debug(f"{self.name} extended effect {effect_name} duration by 2 turns")
            else:
                self.effects.append(Effect(effect_name, 2, 1, self))

            logger.debug(f"{self.name} used card: {self.using.peek().name}")

    def _attack_player(self, target: "Player", immediate: bool = False) -> None:
        """攻击其他玩家的内部实现
        
        Args:
            target: 目标玩家
        """
        if target.health.health <= 0:
            return

        if not self.using.is_empty():
            if self.using.peek() not in (Card("TNT Minecart"),) or immediate:
                logger.debug(f"{self.name} attacking {target.name} with {self.using.peek().name}")
                target.be_attacked(self.using.peek(), self)
            else:
                delay = {
                    "TNT Minecart": 2
                }
                self.game.delay_attack.append((target, self.using.peek(), delay[self.using.peek().name], self))
            
            self.game.card_pool.put_back(self.using.pop())
        else:
            error_msg = f"{self.name} is not using any card"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _handle_delay_attack(self) -> None:
        """处理延迟攻击"""
        if self.delay_attack_this_turn:
            for card, target in self.delay_attack_this_turn:
                self._use_card(card, cheat=True)
                self._attack_player(target, immediate=True)
            self.delay_attack_this_turn = []

    def _try_destroy_bed(self, target: Player) -> None:
        """尝试破坏床"""
        if not target.bed_defence:
            target.bedded = False
        else:
            # 检查using栈是否为空
            if self.using.is_empty():
                logger.error(f"{self.name} tried to destroy bed but no card is being used")
                return
            defence = target.bed_defence[0]
            defence.destroy_by(self.using.peek())
                

    def be_attacked(self, card: Card, attacker: "Player") -> None:
        """处理被攻击逻辑
        
        Args:
            card: 用于攻击的卡牌对象
            attacker: 攻击者对象
        """
        if card.name == "Trident":
            self.cards.append(Card("Damaged Trident", self.game))

        damage_value, damage_type = card.usage()
        if damage_value > 0:
            # 增加攻击力加成
            if hasattr(attacker, "power") and damage_type in ("Physical", ):
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
        self._use_card(card)
        if card.need_target() and other_players:
            target = random.choice(other_players)
            self._attack_player(target)
            action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=str(card), target=target.name)
            logger.debug(action_msg)
            print(action_msg)
        else:
            action_msg = lang("message", "{player} used {card}", player=self.name, card=str(card))
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
                self._use_card(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=str(card))
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
            self._use_card(card)
            other_players.sort(key=lambda p: p.health.health)
            target = other_players[0]
            self._attack_player(target)
            action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=str(card), target=target.name)
            logger.debug(action_msg)
            print(action_msg)
            return True
        return False
    
    def _use_random_non_attack_card(self) -> bool:
        """随机使用非攻击卡牌"""
        non_attack_cards = self._get_non_attack_cards()
        if non_attack_cards:
            card = random.choice(non_attack_cards)
            self._use_card(card)
            action_msg = lang("message", "{player} used {card}", player=self.name, card=str(card))
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
                self._use_card(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=str(card))
                logger.debug(action_msg)
                print(action_msg)
                return True
                
            # 其次使用普通金苹果
            golden_apples = [c for c in self.cards if c.name == "Golden Apple"]
            if golden_apples:
                card = random.choice(golden_apples)
                self._use_card(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=str(card))
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
                self._use_card(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=str(card))
                logger.debug(action_msg)
                print(action_msg)
                return True
        return False
    
    def _use_power_potions(self) -> bool:
        """使用力量药水"""
        power_potions = [c for c in self.cards if c.name == "Potion of Power"]
        if power_potions:
            card = random.choice(power_potions)
            self._use_card(card)
            action_msg = lang("message", "{player} used {card}", player=self.name, card=str(card))
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
                self._use_card(card)
                action_msg = lang("message", "{player} used {card}", player=self.name, card=str(card))
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
                        self._use_card(card)
                        self._attack_player(target)
                        action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=str(card), target=target.name)
                        logger.debug(action_msg)
                        print(action_msg)
                        return True
            
            # 没有能消灭的敌人，使用最高伤害攻击最低生命
            card = attack_cards[0]
            other_players.sort(key=lambda p: p.health.health)
            target = other_players[0]
            self._use_card(card)
            self._attack_player(target)
            action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=str(card), target=target.name)
            logger.debug(action_msg)
            print(action_msg)
            return True
        return False
    
    def _use_random_card(self) -> bool:
        """随机使用一张卡牌"""
        if self.cards:
            card = random.choice(self.cards)
            self._use_card(card)
            other_players = [p for p in self.game.players_in_order if p != self and p.health.health > 0]
            
            # 处理需要目标的卡牌
            if card.need_target() and other_players:
                target = random.choice(other_players)
                self._attack_player(target)
                action_msg = lang("message", "{player} attacks {target} with {card}", player=self.name, card=str(card), target=target.name)
                logger.debug(action_msg)
                print(action_msg)
            elif card.need_target():  # 无可用目标时取消使用
                logger.debug(f"{self.name} canceled card usage (no target)")
                print(lang("message", "{player} did nothing", player=self.name))
                return False
            return True
        return False

    def AI_action(self, other_players):
        if self.AI_level == 0:
            return
        if self.game.get_setting(WAIT_FOR_AI_THINKING):
            time.sleep(random.uniform(1.0, 2.5))
        method_name = f"_ai_level_{self.AI_level}_action"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(other_players)
        else:
            logger.error(f"Method {method_name} not found")

    def info(self, show_cards: bool = True) -> str:
        """返回玩家信息的字符串表示
        
        Args:
            show_cards: 是否显示玩家的卡牌，默认为True
        
        Returns:
            格式为"{player} ({health}, Cards: {cards}, Effects: {effects})"的字符串

    """
        cards = "###"
        if show_cards:
            cards = ", ".join([f"{i}: {card}" for i, card in enumerate(self.cards, 1)])
        return f"{self.name} ({self.health}, Cards: {cards}, Effects: {self.effects})"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Player(name={self.name})"

      
class CardPool:
    """管理卡牌池
    
    Attributes:
        cards (dict[Card, int]): 卡牌列表及其数量
        discard_pile (list[Card]): 废弃卡牌堆
    """

    _default = lambda self, game: {
        Card("Wooden Sword", game): 5,
        Card("Iron Sword", game): 4, 
        Card("Diamond Sword", game): 2, 
        Card("Netherite Sword", game): 1, 
        Card("Wooden Axe", game): 4, 
        Card("Iron Axe", game): 3, 
        Card("Diamond Axe", game): 2, 
        Card("Netherite Axe", game): 1, 
        Card("TNT", game): 3, 
        Card("Apple", game): 4, 
        Card("Golden Apple", game): 2,
        Card("Enchanted Golden Apple", game): 1,
        Card("Potion of Healing", game): 2,
        Card("Potion of Power", game): 1,
        Card("Shield", game): 3,
        Card("Bed", game): 1,
        Card("Trident", game): 3,
        Card("TNT Minecart", game): 3,
        Card("Potion of Instant Damage", game): 2,
        Card("Wooden Pickaxe", game): 5,
        Card("Iron Pickaxe", game): 4,
        Card("Diamond Pickaxe", game): 2,
        Card("Netherite Pickaxe", game): 1,
        Card("Wooden Block", game): 4,
        Card("Stone Block", game): 4,
        Card("Obsidian Block", game): 1,
        Card("Glass", game): 2,
    }

    def __init__(self, cards: dict[Card, int] | None = None, game: Game = None) -> None:
        """初始化卡牌池
        
        Args:
            cards: 卡牌列表及其数量
        """
        # 处理game为None的情况
        if game is None:
            from main import Game  # 延迟导入
            game = Game()

        if cards is None:
            cards = self._default(game)
        self.cards: dict[Card, int] = cards
        self.discard_pile: list[Card] = []  # 废弃卡牌堆
        logger.debug("Card pool initialized")

    def reset(self) -> None:
        """重置卡牌池到初始状态"""
        self.cards = self._default(self.game)
        self.discard_pile = []
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
        logger.debug(f"Added {count}x {str(card)} to card pool")

    def put_back(self, card: Card) -> None:
        """将卡牌放入废弃牌堆
        
        Args:
            card: 要放入废弃牌堆的卡牌
        """
        self.discard_pile.append(card)
        logger.debug(f"Put {card.name} into discard pile")

    def draw_card(self, amount: int = 1) -> list[Card]:
        """从卡牌池中随机抽取卡牌
        
        Args:
            amount: 要抽取的卡牌数量，默认为1
            
        Returns:
            抽取的卡牌列表
        """
        chosen: list[Card] = []
        
        # 如果牌库中的卡牌数量不足，将废弃牌堆洗牌后加入牌库
        total_cards = sum(self.cards.values())
        if total_cards < amount and self.discard_pile:
            logger.debug("Shuffling discard pile back into draw deck")
            # 将废弃牌堆洗牌后加入牌库
            random.shuffle(self.discard_pile)
            for card in self.discard_pile:
                if card in self.cards:
                    self.cards[card] += 1
                else:
                    self.cards[card] = 1
            self.discard_pile = []
            logger.debug(f"Added {len(self.discard_pile)} cards from discard pile to draw deck")
        
        # 如果牌库仍然不足，重置牌库
        total_cards = sum(self.cards.values())
        if total_cards < amount:
            self.reset()
            
        # 抽取卡牌
        for _ in range(amount):
            # 随机选择一张卡牌
            card = random.choice(list(self.cards.keys()))
            # 减少该卡牌的数量
            self.cards[card] -= 1
            if self.cards[card] == 0:
                del self.cards[card]
            chosen.append(card)
            
        logger.debug(f"Drew {amount} cards: {', '.join([c.name for c in chosen])}")
        return chosen

    def __str__(self) -> str:
        """返回卡牌池的字符串表示
        
        Returns:
            卡牌名称及数量的字符串
        """
        card_str = ", ".join(f"{str(card)} x{count}" for card, count in self.cards.items())
        discard_str = lang("message", "Discard: {} cards", len(self.discard_pile))
        return card_str + discard_str
    
    def __add__(self, other: CardPool) -> CardPool:
        """合并两个卡牌池
        
        Args:
            other: 要合并的卡牌池
        
        Returns:
            合并后的卡牌池
        """
        new_pool = CardPool(game=self.game)
        for card, count in self.cards.items():
            new_pool.add_card(card, count)
        for card, count in other.cards.items():
            new_pool.add_card(card, count)
        # 合并废弃牌堆
        new_pool.discard_pile.extend(self.discard_pile)
        new_pool.discard_pile.extend(other.discard_pile)
        logger.debug("Merged two card pools")
        return new_pool



class Game:
    """游戏主类，负责管理游戏状态和流程"""
    
    def __init__(self, players: list[Player] | None = [], *setting_bool: str, **setting_int: int) -> None:
        """
        初始化游戏
        
        Args:
            players: 参与游戏的玩家列表
            setting: 游戏设置

        Note:
            可处理跳过玩家, 直接输入游戏设置的情况
        """
        if isinstance(players, str):
            setting_bool = (*setting_bool, players)
            players = []
        self.players: RepeatQueue[Player] = RepeatQueue(players)
        self.current_player_index: int = 0
        self.is_game_over: bool = False
        self.turn_count: int = 0
        self._current_turn_players: set[Player] = set()
        self.started: bool = False
        self.winner: Player | None = None
        self.card_pool: CardPool = CardPool(game=self)
        self.players_in_order: list[Player] = []
        self.delay_attack: list[tuple[Player, Card, int]] = []
        self.setting_int = setting_int
        self.setting_bool = setting_bool
        logger.debug("Game initialized")

    def get_setting(self, key: str) -> int:
        """获取游戏设置
        
        Args:
            key: 设置键名
        
        Returns:
            对应设置值
        """
        if key in self.setting_int:
            return self.setting_int[key]
        if key in self.setting_bool:
            return 1
        return 0

    def add_player(self, *players: Player) -> None:
        """添加玩家到游戏
        
        Args:
            *players: 一个或多个玩家对象
        """
        for player in players:
            if start_health := self.get_setting("start_health"):
                if start_health <= 0:
                    raise ValueError("start_health must be greater than 0")
                player.health.health = start_health
                player.health.max_health = start_health
            if max_health := self.get_setting("max_health"):
                if max_health < start_health:
                    raise ValueError("max_health must be greater than or equal to start_health")
                player.health.max_health = max_health
            self.players.put(player)
            self.players_in_order.append(player)
            player.game = self
            logger.debug(f"Added player: {player.name} with health {player.health.health}/{player.health.max_health}")

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
        """处理所有玩家的每回合结束逻辑"""
        if not self.players:
            logger.error("No players found for after_turn processing")
            print("No players found!")
            return

        logger.debug("Processing after-turn effects for all players")
        for player in self.players:
            player.after_turn()

        self._handle_delay_attack()

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

    def _handle_card_selection(self, player: Player, condition: Callable[[Card], bool] = lambda _: True) -> Card | None:
        """处理卡牌选择
        
        Args:
            player: 当前玩家
            
        Returns:
            选择的卡牌或None
        """
        cards = [card for card in player.cards if condition(card)]

        # 本地化显示玩家手牌
        cards_list = [f"{i}: {card}" for i, card in enumerate(cards, 1)]
        cards_msg = lang("message", "Available Cards: {}", ", ".join(cards_list))
        logger.debug(cards_msg)
        print(cards_msg)

        if not player.cards:
            no_cards_msg = lang("message", "No cards left in {player}'s hand", player=player.name)
            logger.debug(no_cards_msg)
            print(no_cards_msg)
            player.add_card(*self.card_pool.draw_card(5))
            return None
            
        # 本地化输入提示
        card_index = input(lang("message", "Enter card index to use: "))

        try:
            card = cards[int(card_index) - 1]
            logger.debug(f"{player.name} selected card: {card.name}")
            return card
        except:
            error_msg = lang("message", "Invalid card index")
            logger.fatal(error_msg)
            print(error_msg)
            raise ValueError(error_msg)

    def _handle_target_selection(self, player: Player, card: Card, condition: Callable[[Player], bool] = lambda _: True) -> Player | None:
        """处理目标选择
        
        Args:
            player: 当前玩家
            card: 使用的卡牌
            condition: 目标玩家必须满足的条件

        Returns:
            选择的目标玩家或None
        """
        targets = [p for p in self.players_in_order if p != player and p.health.health > 0 and condition(p)]
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

            player.AI_action([p for p in self.players_in_order if p != player])

            if messages["defence_break"]:
                print(messages["defence_break"])

            if messages["death"]:
                print(messages["death"])

            print()
        else:
            self._handle_human_turn(player)

        player._handle_delay_attack()

    def _handle_action_choose(self, player: Player) -> str:
        """处理玩家回合选择
        
        Args:
            player: 当前回合的玩家
        """
        actions = ["attack/use", "draw 2 cards"]
        for card in player.list_cards():
            if card.destroy_defense_type() != DESTROY_NONE:
                actions.append("destroy/defend bed")
                break

        print(lang("message", "Actions: "), end="")
        for i, action in enumerate(actions, 1):
            print(f"{i}: {lang("actions", action)}", end=", " if i < len(actions) else "\n")
        action = input(lang("message", "Enter action index: "))
        print()
        return actions[int(action) - 1]
            
    def _handle_human_turn(self, player: Player) -> None:
        """处理人类玩家回合
        
        Args:
            player: 当前回合的人类玩家
        """
        messages = {}
        messages.setdefault("death", "")
        messages.setdefault("defence_break", "")
        
        self._display_player_status(player)

        if player.AI_level:
            return

        # 本地化显示玩家手牌
        cards_list = [f"{str(card)}" for card in player.cards]
        cards_msg = lang("message", "Cards: {}", ", ".join(cards_list))
        logger.debug(cards_msg)
        print(cards_msg)
        print()

        action = self._handle_action_choose(player)
        {
            "attack/use": self.attack_or_use_card,
            "draw 2 cards": self.draw_2_cards,
            "destroy/defend bed": self.destroy_defend_bed,
        }[action](player)

    def attack_or_use_card(self, player: Player) -> None:
        """攻击或使用卡牌"""
        # 处理卡牌选择
        card = self._handle_card_selection(player, lambda card: card.destroy_defense_type() != DESTROY_PICKAXE)
        if card is None:
            return
            
        player._use_card(card)

        if card.need_target():
            # 处理目标选择
            target = self._handle_target_selection(player, card)
            if target is None:
                return
            player._attack_player(target)

            if messages.get("defence_break"):
                print(messages["defence_break"])
            if messages.get("death"):
                print(messages["death"])
        else:
            # 本地化使用卡牌消息
            card_use_msg = lang("message", "{player} used {card}", player=player.name, card=str(card))
            logger.debug(card_use_msg)
            print(card_use_msg)

        print()

    def draw_2_cards(self, player: Player) -> None:
        """抽2张牌"""
        logger.debug(f"{player.name} drew 2 cards")
        drawn_cards = self.card_pool.draw_card(2)
        player.add_card(*drawn_cards)
        # 本地化抽牌消息
        draw_msg = lang("message", "{player} drew {count} cards: {cards}", player=player.name, count=len(drawn_cards), cards=", ".join(str(card) for card in drawn_cards))
        logger.debug(draw_msg)
        print(draw_msg)
        print()
        return None
            

    def destroy_defend_bed(self, player: Player) -> None:
        """破坏/守护床"""
        # 处理卡牌选择
        card = self._handle_card_selection(player, lambda card: card.destroy_defense_type() != DESTROY_NONE)
        if card is None:
            return

        target = self._handle_target_selection(player, card)
        if target is None:
            return

        player._use_card(card)

        if card.destroy_defense_type()[1] < 0:
            player._try_destroy_bed(target)
        else:
            player.bed_defence.push(BedDefenceFromCard(card, player))

        # 本地化破坏床消息
        destroy_msg = lang("message", "{player} destroyed bed of {target}", player=player.name, target=target.name)
        logger.debug(destroy_msg)
        print(destroy_msg)
        print()

    def _handle_delay_attack(self) -> None:
        """处理延迟攻击"""
        new_list = []
        for target, card, delay, attacker in self.delay_attack:
            if delay > 1:
                new_list.append((target, card, delay - 1, attacker))
            else:
                if attacker.health.health > 0:
                    attacker.delay_attack_this_turn.append((card, target))
        
        self.delay_attack = new_list
        
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
            if self.get_setting(DEBUG):
                print(self.delay_attack)

            player = self.players.peek()
            if player.health.health <= 0:
                self.players.remove(player)
                continue
                
            self._handle_player_turn(player)
            
            if self._is_turn_finished():
                self.after_turn()

            if self.get_setting(EXIT_ON_ALL_HUMAN_DEAD) and self._check_human_dead():
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

    game = Game(EXIT_ON_ALL_HUMAN_DEAD, MAX_HEALTH=7)
    game.add_player(*(Player("") for _ in range(2)))
    # game.add_player(*(Player("", 3) for _ in range(0)))

    for _ in range(0):
        game.card_pool += game.card_pool

    game.start()
    logger.debug("Game ended")

def AI_competition():
    log_clear()

    logger.debug("AI competition starting")
    set_language("zh_cn")
    
    game = Game()

    players = []
    AI = ["ds", "db", "km", "ty"] # ds: DeepSeek, db: Doubao, km: Kimi, ty: TongYi
    for ai in AI:
        players.extend((Player(ai + str(i + 1)) for i in range(4)))

    random.shuffle(players)
    game.add_player(*players)

    for _ in range(2):
        game.card_pool += game.card_pool

    game.start()

    logger.debug("Game ended")

def test():
    player1 = Player("p1")
    player2 = Player("p2")
    
    player1.bedded = True
    player1.bed_defence.push(BedDefence("test", DEFENCE_STONE, parent_class=player1))

    player2.cards.append(Card("Wooden Pickaxe"))
    player2.cards.append(Card("Wooden Pickaxe"))

    player2._use_card(player2.cards[0])
    player2._try_destroy_bed(player1)
    print(player1.bed_defence)

    player2._use_card(player2.cards[0])
    player2._try_destroy_bed(player1)
    print(player1.bedded)

if __name__ == "__main__":
    main()