import os
import subprocess

def main():
    print("=== Minecraft Server Launcher by Om Prakash ===")
    print("Select server type:")
    print("1. Vanilla (server.jar)")
    print("2. Pocket Edition (pocketmine-mp.phar)")
    print("3. Fabric (fabric-server-launch.jar)")
    print("4. Forge (forge-server.jar)")
    print("5. Paper MC (papermc.jar)")
    print("6. Custom JAR")
    
    choice = input("Enter choice (1-5): ")

    jar_file = "server.jar"  # Default

    if choice == "1":
        jar_file = "server.jar"
    elif choice == "2":
        jar_file = "pocketmine-mp.phar"
    elif choice == "3":
        jar_file = "fabric-server-launch.jar"
    elif choice == "4":
        jar_file = "forge-server.jar"
    elif choice == "5":
        jar_file = "papermc.jar"
    elif choice == "6":
        jar_file = input("Enter the custom server .jar/.phar file name: ")
    else:
        print("Invalid choice.")
        return

    if not os.path.isfile(jar_file):
        print(f"Error: '{jar_file}' not found in the current directory.")
        return

    print(f"Launching server using '{jar_file}'...\n")

    # Optional: Change the console title (Windows only)
    os.system(f"title Minecraft Server - {jar_file}")

    # Launch the server
    if jar_file.endswith(".phar"):
        # PocketMine usually uses PHP (for Windows users with PHP installed)
        subprocess.run(["php", jar_file])
    else:
        subprocess.run(["java", "-jar", jar_file, "gui"])

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
