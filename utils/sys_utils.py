def print_task(task_number, description=None):
    title = f"## TASK {task_number} ##"
    border = "#" * len(title)
    
    print(border)
    print(title)
    print(border)
    
    if description:
        print(f"Description: {description}")
    
    print("-\n-")