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