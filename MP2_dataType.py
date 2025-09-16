from typing import TypeVar, Generic

# 定义泛型类型T
T = TypeVar('T')

class Queue(Generic[T]):
    """基础队列实现"""
    
    def __init__(self, items: list[T] | None = None):
        """初始化队列
        
        Args:
            items: 初始元素列表，默认为空
        """
        self.items = items or []

    def __getindex__(self, index: int) -> T:
        """获取指定索引的元素
        
        Args:
            index: 元素索引
            
        Returns:
            指定索引的元素
        """
        return self.items[index]

    def is_empty(self) -> bool:
        """检查队列是否为空
        
        Returns:
            bool: 如果队列为空返回True，否则False
        """
        return self.items == []
    
    def put(self, item: T) -> None:
        """向队列尾部添加元素
        
        Args:
            item: 要添加的元素
        """
        self.items.append(item)

    def peek(self) -> T:
        """查看并移除队列头部元素
        
        Returns:
            队列头部元素
            
        Raises:
            IndexError: 如果队列为空
        """
        if self.is_empty():
            raise IndexError("Queue is empty")
        else:
            return self.items.pop(0)

    def front(self) -> T:
        """查看但不移除队列头部元素
        
        Returns:
            队列头部元素
            
        Raises:
            IndexError: 如果队列为空
        """
        if self.is_empty():
            raise IndexError("Queue is empty")
        else:
            return self.items[0]
        
    def __len__(self) -> int:
        """获取队列长度
        
        Returns:
            队列中元素的数量
        """
        return len(self.items)
    
    def __iter__(self):
        """返回队列的迭代器
        
        Returns:
            队列的迭代器
        """
        return iter(self.items)

    def __getitem__(self, index: int) -> T:
        """通过索引获取队列元素
        
        Args:
            index: 元素索引
            
        Returns:
            指定索引的元素
        """
        return self.items[index]
    
    def remove(self, item: T) -> None:
        """从队列中移除指定元素
        
        Args:
            item: 要移除的元素
        """
        self.items.remove(item)

class RepeatQueue(Queue[T]):
    """可重复使用的队列，peek操作不会移除元素"""
    
    def peek(self) -> T:
        """查看但不移除队列头部元素，并将其添加到队列尾部
        
        Returns:
            队列头部元素
            
        Raises:
            IndexError: 如果队列为空
        """
        if self.is_empty():
            raise IndexError("Queue is empty")
        else:
            self.put(self.items[0])  # 将头部元素添加到尾部
            return self.items.pop(0)  # 移除并返回头部元素

class Stack(Queue[T]):
    """栈实现"""
    
    def peek(self) -> T:
        """查看但不移除栈顶元素
        
        Returns:
            栈顶元素
            
        Raises:
            IndexError: 如果栈为空
        """
        if self.is_empty():
            raise IndexError("Stack is empty")
        else:
            return self.items[-1]

    def __str__(self) -> str:
        """返回栈的字符串表示
        
        Returns:
            栈的字符串表示
        """
        return str(self.items)

    def push(self, item: T) -> None:
        """向栈顶添加元素
        
        Args:
            item: 要添加的元素
        """
        self.items.append(item)
    
    def pop(self) -> T:
        """移除并返回栈顶元素
        
        Returns:
            栈顶元素
            
        Raises:
            IndexError: 如果栈为空
        """
        if self.is_empty():
            raise IndexError("Stack is empty")
        else:
            return self.items.pop()
    
    def __len__(self) -> int:
        """获取栈长度
        
        Returns:
            栈中元素的数量
        """
        return len(self.items)
    
    def __iter__(self):
        """返回栈的迭代器
        
        Returns:
            栈的迭代器
        """
        return iter(self.items)

    def is_empty(self) -> bool:
        """检查栈是否为空
        
        Returns:
            bool: 如果栈为空返回True，否则False
        """
        return self.items == []

    def __bool__(self) -> bool:
        """检查栈是否为空
        
        Returns:
            bool: 如果栈为空返回False，否则True
        """
        return not self.is_empty()

class BetterFloat:
    """自定义浮点数类, 使用十进制科学计数, 法用于处理浮点数的比较"""
    def __init__(self, value: int | str, exp: int = 0) -> None:
        if isinstance(value, str):
            if '.' in value:
                fractional_part = value.split('.')[1]
                self.value = int(value.replace('.', ''))
                self.exp = -len(fractional_part)
            else:
                self.value = int(value)
                self.exp = 0
            return

        if not isinstance(value, int):
            raise TypeError(f"value must be int, not {type(value).__name__}")
        if not isinstance(exp, int):
            raise TypeError(f"exp must be int, not {type(exp).__name__}")
        self.exp: int = exp
        self.value: int = value

    def __float__(self) -> float:
        """将自定义浮点数转换为标准浮点数
        
        Returns:
            float: 转换后的浮点数
        """
        return 10 ** self.exp * float(self.value)

    def __str__(self) -> str:
            """返回自定义浮点数的字符串表示
            
            Returns:
                str: 自定义浮点数的字符串表示
            """
            if self.exp < 0:
                s = str(self.value)
                n = -self.exp
                
                # 处理负数情况
                if s[0] == '-':
                    negative = True
                    s = s[1:]
                else:
                    negative = False
                
                # 需要补零的情况
                if n >= len(s):
                    integer_part = '0'
                    fractional_part = '0' * (n - len(s)) + s
                else:
                    integer_part = s[:-n] or '0'  # 如果整数部分为空，设为'0'
                    fractional_part = s[-n:]
                
                # 还原负号
                if negative:
                    integer_part = '-' + integer_part
                
                # 组合结果
                if fractional_part:
                    return f"{integer_part}.{fractional_part}"
                else:
                    return integer_part
                    
            elif self.exp > 0:
                return str(self.value) + '0' * self.exp
            else:
                return str(self.value)

    def __repr__(self) -> str:
        """返回自定义浮点数的字符串表示
        
        Returns:
            str: 自定义浮点数的字符串表示
        """
        return f"{self.value}e{self.exp}"

    def shift(self, exp: int) -> None:
        """将浮点数的指数部分向右移动exp位
        
        Args:
            exp: 移动的位数
        """
        if exp == 0:
            return

        self.exp += exp
        if exp > 0:
            self.value = int(str(self.value) + '0' * exp)
        else:
            try:
                self.value = int(str(self.value)[:len(str(self.value)) + exp])
            except ValueError:
                self.value = 0

    def __add__(self, other: "BetterFloat") -> "BetterFloat":
        """自定义浮点数加法
        
        Args:
            other: 另一个浮点数
            
        Returns:
            加法结果
        """
        this = BetterFloat(self.value, self.exp)
        if this.exp == other.exp:
            this.value += other.value
            return this

        if this.exp < other.exp:
            other.shift(other.exp - this.exp)
        else:
            this.shift(this.exp - other.exp)
        this.value += other.value
        return this

    def __sub__(self, other: "BetterFloat") -> "BetterFloat":
            """自定义浮点数减法
            
            Args:
                other: 另一个浮点数
                
            Returns:
                减法结果
            """
            other = BetterFloat(- other.value, other.exp)
            return self + other

if __name__ == "__main__":
    a = BetterFloat(1, -1)
    b = BetterFloat(21, -1)
    print(a + b)

    c = BetterFloat('0.2')
    print(c + a)