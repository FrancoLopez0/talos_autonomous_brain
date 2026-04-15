from langchain.tools import tool
import numexpr as ne

@tool
def calculate(expresion: str) -> str:
    """
    Evalúa operaciones matemáticas puras y devuelve el resultado.
    Usa solo sintaxis de Python (ej. usa ** para potencias en lugar de ^).
    Ejemplos válidos: "2 + 2", "sqrt((2.5 - 10.0)**2 + (2.5 - 2.0)**2)"
    """
    try:
        # Los LLMs a veces insisten en usar ^ para potencias, lo corregimos a **
        expresion_limpia = expresion.replace("^", "**")
        

        # numexpr evalúa el string de forma rápida y súper segura
        resultado = ne.evaluate(expresion_limpia)
        
        print(f"Calculando la expresión: {expresion_limpia} = {resultado}")

        # Convertimos el resultado a float y luego a string para devolvérselo al agente
        return f"Resultado de la operación: {float(resultado)}"
        
    except Exception as e:
        return f"Error en la fórmula matemática: {str(e)}. Por favor revisa la sintaxis."