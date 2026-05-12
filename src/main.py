import os
import sys
import logging


def show_menu():
    print("Sistema Enoc - Obtencion de informacion Actualizada")
    print("Menu:")
    print("1. Option 1 - Obetencion de informacion Noticias")
    print("2. Option 2 - Obetencion de informacion Precios")
    print("3. Option 3 - Obetencion de informacion Clima")
    print("4. Option 4 - Obetencion de informacion Trabajos")
    print("5. Option 5 - Obetencion de informacion Economia")
    print("6. Option 6 - Obetencion de informacion Tecnologia")
    print("7. Option 7 - Obetencion de informacion Salud")
    print("8. Option 8 - Obetencion de informacion Entretenimiento")
    print("9. Option 9 - Obetencion de informacion Cultura")
    print("10. Option 10 - Seguimiento de Inversiones")
    print("11. Option 11 - Alertas de Ofertas en Tecnología (MarketPlace)")
    print("12. Option 12 - Monitoreo de Precios de Vuelos ")
    print("13. Option 13 - Licitaciones Públicas")
    print("14. Option 14 - Monitor de Gasolineras")
    print("15. Option 15 - Noticias Qa")
    print("16. Option 16 - Testing")
    print("17. Exit")


def execute_option(option):
    if option == "1":
        print("Obteniendo información de Noticias...")
        # Lógica para obtener información de noticias
    elif option == "2":
        print("Obteniendo información de Precios...")
        # Lógica para obtener información de precios
    elif option == "3":
        print("Obteniendo información de Clima...")
        # Lógica para obtener información de clima
    elif option == "4":
        print("Obteniendo información de Trabajos...")
        # Lógica para obtener información de trabajos
    elif option == "5":
        print("Obteniendo información de Economía...")
        # Lógica para obtener información de economía
    elif option == "6":
        print("Obteniendo información de Tecnología...")
        # Lógica para obtener información de tecnología
    elif option == "7":
        print("Obteniendo información de Salud...")
        # Lógica para obtener información de salud
    elif option == "8":
        print("Obteniendo información de Entretenimiento...")
        # Lógica para obtener información de entretenimiento
    elif option == "9":
        print("Obteniendo información de Cultura...")
        # Lógica para obtener información de cultura
    elif option == "10":
        print("Realizando seguimiento de inversiones...")
        # Lógica para seguimiento de inversiones
    elif option == "11":
        print("Obteniendo alertas de ofertas en tecnología (MarketPlace)...")
        # Lógica para alertas de ofertas en tecnología
    elif option == "12":
        print("Monitoreando precios de vuelos...")
        # Lógica para monitoreo de precios de vuelos
    elif option == "13":
        print("Obteniendo licitaciones públicas...")
        # Lógica para licitaciones públicas
    elif option == "14":
        print("Monitoreando gasolineras...")
        # Lógica para monitoreo de gasolineras
    elif option == "15":
        print("Obteniendo noticias QA...")
        # Lógica para noticias QA
    elif option == "16":
        print("Ejecutando pruebas...")
        # Lógica para testing
    elif option == "17":
        print("Saliendo del sistema. ¡Hasta luego!")
        sys.exit(0)
    else:
        print("Opción no válida. Por favor, seleccione una opción del menú.")


def main():
    while True:
        show_menu()
        option = input("Seleccione una opción: ")
        execute_option(option)

if __name__ == "__main__":
    main()



