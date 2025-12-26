from tortoise.expressions import Q
from tortoise.transactions import atomic

from app.core.crud import CRUDBase
from app.models.admin import Dept, DeptClosure
from app.schemas.depts import DeptCreate, DeptUpdate


class DeptController(CRUDBase[Dept, DeptCreate, DeptUpdate]):
    def __init__(self):
        super().__init__(model=Dept)

    async def get_dept_tree(self, name):
        q = Q()
        # 获取所有未被软删除的部门
        q &= Q(del_flag="0")
        if name:
            q &= Q(dept_name__icontains=name)
        all_depts = await self.model.filter(q).order_by("order_num")

        # 辅助函数，用于递归构建部门树
        def build_tree(parent_id):
            return [
                {
                    "id": dept.id,
                    "name": dept.dept_name,
                    "desc": dept.desc,
                    "order_num": dept.order_num,
                    "parent_id": dept.parent_id,
                    "children": build_tree(dept.id),  # 递归构建子部门
                }
                for dept in all_depts
                if dept.parent_id == parent_id
            ]

        # 从顶级部门（parent_id=0）开始构建部门树
        dept_tree = build_tree(0)
        return dept_tree

    async def get_dept_info(self):
        pass

    async def update_dept_closure(self, obj: Dept):
        """
        更新部门层级关系表
        
        Args:
            obj: 部门对象
        """
        # 严格的类型检查
        if not isinstance(obj, Dept):
            raise ValueError(f"Expected Dept instance, got {type(obj)}")
        
        # 确保obj已保存到数据库
        if not hasattr(obj, '_saved_in_db') or not obj._saved_in_db:
            # 尝试重新获取对象以确保它是有效的数据库实例
            if obj.id:
                try:
                    # 使用get()方法确保返回单个实例
                    fresh_obj = await Dept.get(id=obj.id)
                    # 立即验证类型
                    if not isinstance(fresh_obj, Dept):
                        raise ValueError(f"Retrieved object is not a Dept instance: {type(fresh_obj)}")
                    obj = fresh_obj
                except Exception as e:
                    raise ValueError(f"Failed to retrieve department with ID {obj.id}: {e}")
            else:
                raise ValueError(f"Department object has no ID")
        
        # 最终验证obj类型
        if not isinstance(obj, Dept):
            raise ValueError(f"Object is not a Dept instance before creating closure: {type(obj)}")
        
        # 首先为自己创建一个自引用的闭包记录（level=0）
        await DeptClosure.create(ancestor=obj, descendant=obj, level=0)
        
        # 如果有父部门，需要继承父部门的所有祖先关系
        if obj.parent_id and obj.parent_id != 0:
            # 确保父部门存在
            try:
                parent_dept = await Dept.filter(id=obj.parent_id).first()
                if not parent_dept:
                    raise ValueError(f"Parent department with ID {obj.parent_id} not found")
                
                # 验证父部门是Dept实例
                if not isinstance(parent_dept, Dept):
                    raise ValueError(f"Parent dept is not a Dept instance: {type(parent_dept)}")
                
            except Exception as e:
                raise ValueError(f"Failed to get parent department with ID {obj.parent_id}: {e}")
            
            # 获取父部门的所有祖先关系（包括父部门自己）
            parent_closures = await DeptClosure.filter(descendant=parent_dept).values('ancestor_id', 'level')
            
            for closure_data in parent_closures:
                ancestor_id = closure_data['ancestor_id']
                closure_level = closure_data['level']
                
                # 验证ancestor_id是有效的整数
                if not isinstance(ancestor_id, int) or ancestor_id <= 0:
                    continue
                
                # 获取祖先部门对象
                try:
                    # 使用更安全的查询方式，确保返回单个实例
                    ancestor_dept = await Dept.filter(id=ancestor_id).first()
                    if not ancestor_dept:
                        raise ValueError(f"Ancestor department with ID {ancestor_id} not found")
                    
                    # 严格的类型检查
                    if not isinstance(ancestor_dept, Dept):
                        raise ValueError(f"Ancestor dept is not a Dept instance: {type(ancestor_dept)}")
                    
                    # 确保对象已保存到数据库
                    if not hasattr(ancestor_dept, '_saved_in_db') or not ancestor_dept._saved_in_db:
                        raise ValueError(f"Ancestor department {ancestor_dept.id} is not saved to database")
                    
                    # 再次验证obj仍然是Dept实例
                    if not isinstance(obj, Dept):
                        raise ValueError(f"Descendant obj is not a Dept instance: {type(obj)}")
                    
                    # 确保obj已保存到数据库
                    if not hasattr(obj, '_saved_in_db') or not obj._saved_in_db:
                        raise ValueError(f"Department {obj.id} is not saved to database")
                    
                    # 为当前部门创建与祖先的关系，层级+1
                    new_level = closure_level + 1
                    
                    # 在DeptClosure.create调用前再次验证类型
                    if not isinstance(obj, Dept):
                        raise ValueError(f"Descendant object is not a Dept instance: {type(obj)}")
                    if not isinstance(ancestor_dept, Dept):
                        raise ValueError(f"Ancestor object is not a Dept instance: {type(ancestor_dept)}")
                    
                    await DeptClosure.create(
                        ancestor=ancestor_dept,
                        descendant=obj,
                        level=new_level
                    )
                        
                except Exception as e:
                    continue

    async def create_dept(self, obj_in: DeptCreate):
        # 创建
        if obj_in.parent_id != 0:
            try:
                await self.get(id=obj_in.parent_id)
            except Exception as e:
                print(f"Error: Parent department with ID {obj_in.parent_id} not found. {e}")
                raise
        new_obj = await self.create(obj_in=obj_in)
        await self.update_dept_closure(new_obj)
        return new_obj

    @atomic()
    async def update_dept(self, obj_in: DeptUpdate):
        dept_obj = await self.get(id=obj_in.id)
        # 更新部门关系
        if dept_obj.parent_id != obj_in.parent_id:
            await DeptClosure.filter(ancestor=dept_obj.id).delete()
            await DeptClosure.filter(descendant=dept_obj.id).delete()
            await self.update_dept_closure(dept_obj)
        # 更新部门信息
        dept_obj.update_from_dict(obj_in.model_dump(exclude_unset=True))
        await dept_obj.save()

    @atomic()
    async def delete_dept(self, dept_id: int):
        # 删除部门
        obj = await self.get(id=dept_id)
        obj.del_flag = "1"
        await obj.save()
        # 删除关系
        await DeptClosure.filter(descendant=dept_id).delete()


dept_controller = DeptController()
