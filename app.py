# Simple Inventory Management System

inventory = []

def add_item():
    name = input("Enter item name: ")
    quantity = int(input("Enter quantity: "))
    inventory.append({"name": name, "quantity": quantity})
    print("Item added successfully!\n")

def view_items():
    if not inventory:
        print("Inventory is empty.\n")
    else:
        print("\nInventory List:")
        for i, item in enumerate(inventory):
            print(f"{i}. {item['name']} - {item['quantity']}")
        print()

def update_item():
    view_items()
    index = int(input("Enter item index to update: "))
    if 0 <= index < len(inventory):
        name = input("Enter new name: ")
        quantity = int(input("Enter new quantity: "))
        inventory[index] = {"name": name, "quantity": quantity}
        print("Item updated successfully!\n")
    else:
        print("Invalid index.\n")

def delete_item():
    view_items()
    index = int(input("Enter item index to delete: "))
    if 0 <= index < len(inventory):
        inventory.pop(index)
        print("Item deleted successfully!\n")
    else:
        print("Invalid index.\n")

def menu():
    while True:
        print("=== Inventory Management System ===")
        print("1. Add Item")
        print("2. View Items")
        print("3. Update Item")
        print("4. Delete Item")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_item()
        elif choice == "2":
            view_items()
        elif choice == "3":
            update_item()
        elif choice == "4":
            delete_item()
        elif choice == "5":
            print("Exiting program...")
            break
        else:
            print("Invalid choice. Try again.\n")

menu()
