from typing import Self

class Card:
    """表示游戏中的卡牌，包含卡牌名称和使用效果
    
    Attributes:
        name (str): 卡牌名称，只能包含字母数字，最长20个字符
    """
    def __init__(self, name: str) -> None:
        """初始化卡牌
        
        Args:
            name: 卡牌名称
            
        Raises:
            TypeError: 如果名称不是字符串
            ValueError: 如果名称包含非字母数字字符或长度超过20
        """
        if not isinstance(name, str):
            raise TypeError("Card name must be a string")
        # 允许字母、数字和空格，但必须至少有一个非空格字符
        if not all(c.isalnum() or c.isspace() for c in name) or not name.strip():
            raise ValueError("Card name can only contain alphanumeric characters and spaces")
        if len(name) > 20:
            raise ValueError("Card name too long (max 20 characters)")
        self.name: str = name

    def __str__(self) -> str:
        """返回卡牌的字符串表示形式
        
        Returns:
            卡牌名称
        """
        return self.name

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

    def usage(self) -> tuple[int, str]:
        """获取卡牌的使用效果
        
        Returns:
            tuple: (伤害值, 伤害类型)
                  伤害值为0表示无伤害效果
        """
        if self.name.endswith("Sword"):
            quality = self.name[:-5]
            damage = {"Wood": 1, "Iron": 2, "Diamond": 3, "Netherite": 4}[quality]
            return (damage, "physical")
        if self.name.endswith("Axe"):
            quality = self.name[:-3]
            damage = {"Wood": 1, "Iron": 2, "Diamond": 3, "Netherite": 4}[quality]
            return (damage, "physical")
        if self.name == "TNT":
            return (3, "explosive")
        # TODO


        return (0, "")

def defendable(defence: str | None, damageType: str) -> bool:
    if not defence:
        return False
    if defence == "Shield":
        return damageType not in ("magical", "explosive") # 可抵挡所有伤害(除了magical和explosive)，但会被爆炸或斧头破坏
    # TODO
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
        
        # 先再进行防御判断
        if defendable(self.defence, damage.type) and self.defence_times > 0:
            self.defence_times -= 1
            if self.defence_times == 0:
                self.defence = None
        else:
            self.health -= damage.damage
            if self.health <= 0:
                print(f"{self.parent_class.name} is dead")

        # 再处理所有破坏条件
        if self.defence == "Shield":
            if damage.item.endswith("Axe") or damage.type == "explosive":
                self.defence_times = 0
                self.defence = None

        return self
    
class Effect:
    """表示游戏中的效果
    
    Attributes:
        name (str): 效果名称
        duration (int): 持续时间
    """
    def __init__(self, name: str, duration: int, parent_class: "Player") -> None:
        """初始化效果
        
        Args:
            name: 效果名称
            duration: 持续时间
            parent_class: 所属玩家对象

        Raises:
            ValueError: 如果名称不是"Potion of"开头(即效果名称不符合规则)
        """
        if name.startswith("Potion of"):
            self.name: str = name[9:].strip().lower()
            self.duration: int = duration
            self.parent_class: Player = parent_class
        else:
            raise ValueError(f"Invalid effect name: {name}")

    def __str__(self) -> str:
        """返回效果的字符串表示
        
        Returns:
            格式为"{name} ({duration} turns)"的字符串
        """
        return f"{self.name} ({self.duration} turns)"
    
    def effect(self):
        """"""
        if self.name == "healing":
            self.parent_class.health.health += 1
        elif self.name == "power":
            self.parent_class.power = 1

        self.duration -= 1
        if self.duration == 0:
            self.parent_class.effects.remove(self)
            del self

        

class Player:
    """表示游戏玩家，包含玩家状态和卡牌操作
    
    Attributes:
        name (str): 玩家名称
        health (Health): 玩家生命值状态
        cards (list[Card]): 玩家持有的卡牌列表
        using (Card | None): 当前正在使用的卡牌
    """
    def __init__(self, name: str) -> None:
        """初始化玩家
        
        Args:
            name: 玩家名称
        """
        self.name: str = name
        self.health: Health = Health(5, self)
        self.cards: list[Card] = []
        self.using: Card | None = None
        self.effects: list[Effect] = []
        self.power: int = 0  # 增加玩家的攻击力

    def __str__(self) -> str:        
        """返回玩家信息的字符串表示
        
        Returns:
            格式为"{name} ({health})"的字符串
        """
        return f"{self.name} ({self.health})"
    
    def after_turn(self) -> None:        
        """处理玩家的每回合结束逻辑"""
        self.power = 0
        for effect in self.effects:
            effect.effect()


    def add_card(self, card: Card, count: int = 1) -> None:
        """添加卡牌到玩家手牌
        
        Args:
            card: 要添加的卡牌对象
            count: 要添加的数量，默认为1
        """
        for _ in range(count):
            self.cards.append(card)

    def __call__(self, card_or_target: Card | Self | None = None) -> None:
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
            if self.using:
                self.cards.append(self.using)
                self.using = None
            if card_or_target in self.cards:
                self.cards.remove(card_or_target)
                self.using = card_or_target
                if self.using.name in ("Shield", "Apple"):
                    if self.using.name == "Shield":
                        self.health.defence = self.using.name
                        self.health.defence_times = 3
                    if self.using.name == "Apple":
                        self.health.health += 1
                elif self.using.name.startswith("Potion of"):
                    self.effects.append(Effect(self.using.name, 2, self))
            else:
                raise ValueError(f"Card {card_or_target.name} not in {self.name}'s hand")

        elif isinstance(card_or_target, Player):
            if self.using is not None:
                card_or_target.be_attacked(self.using, self)

                self.using = None
            else:
                raise ValueError("Player is not using any card")
            
        elif card_or_target is None:
            pass
            
        else:
            raise TypeError("Invalid argument type")
        
    def be_attacked(self, card: Card, attacker: Self) -> None:
        """处理被攻击逻辑
        
        Args:
            card: 用于攻击的卡牌对象
            attacker: 攻击者对象
        """
        damage_value, damage_type = card.usage()
        if damage_value > 0:
            # 增加攻击力加成
            if hasattr(attacker, 'power'):
                damage_value += attacker.power
            self.health -= Damage(damage_value, damage_type, card.name)

def after_turn() -> None:
    """处理所有玩家的每回合结束逻辑"""
    global player_list
    for player in player_list:
        player.after_turn()

at = after_turn
            

if __name__ == "__main__":
    """测试游戏逻辑"""
    # 创建两个玩家
    player1 = Player("Player1")
    player2 = Player("Player2")

    player_list = [player1, player2]

    # 创建攻击卡(各种剑)
    card1 = Card("WoodSword")
    card2 = Card("IronSword")
    card3 = Card("IronAxe")
    card4 = Card("NetheriteSword")

    TNT_card = Card("TNT")

    # 创建防御卡和治疗卡
    shield_card = Card("Shield")
    apple_card = Card("Apple")

    potion_card1 = Card("Potion of Power")
    potion_card2 = Card("Potion of Healing")

    player1.add_card(card1)
    player1.add_card(card2)
    player1.add_card(card3)
    player1.add_card(card4)
    player1.add_card(TNT_card)
    player1.add_card(potion_card1)

    player2.add_card(shield_card)
    player2.add_card(apple_card)
    player2.add_card(potion_card2)

    # 测试第一次攻击(无防御)
    player1(card1)
    player1(player2)
    print(player2.health)

    # 测试防御效果(激活护盾)
    player2(shield_card)

    at()

    # 第二次攻击
    player1(card2)
    player1(player2)
    print(player2.health)

    # 测试治疗效果(吃苹果)
    player2(apple_card)
    print(player2.health)

    at()

    # 测试爆炸效果(使用TNT)
    player1(TNT_card)
    player1(player2)
    print(player2.health)

    player2(potion_card2)
    print(player2.health)

    at()  # 回合结束, 药效生效
    print(player2.health)

    # 测试使用药水效果(增加攻击力)
    player1(potion_card1)

    player2()

    at()  # 回合结束, 药效生效并消失

    print(player2.effects)
    print(player2.health)

    player1(card4)
    player1(player2)
    print(player2.health)
