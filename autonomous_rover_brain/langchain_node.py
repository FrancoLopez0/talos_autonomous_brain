import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage
import os


class LangchainNode(Node):
    def __init__(self):
        super().__init__('langchain_node')
        
        # 1. Configurar Publicador y Suscriptor
        self.subscription = self.create_subscription(
            String,
            '/llm_prompt',
            self.prompt_callback,
            10
        )
        self.publisher_ = self.create_publisher(String, '/llm_response', 10)


        # Al inicio del __init__
        self.declare_parameter('model', 'default_model')
        self.declare_parameter('max_tokens', 512)

        # Al momento de usar LangChain
        modelo_actual = self.get_parameter('model').get_parameter_value().string_value
        tokens = self.get_parameter('max_tokens').get_parameter_value().integer_value
        
        # 2. Inicializar el modelo de Langchain
        # Asegúrate de tener la variable de entorno OPENAI_API_KEY configurada
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            self.get_logger().error("No se encontró OPENROUTER_API_KEY en las variables de entorno.")
            
        self.get_logger().info("Inicializando modelo Langchain (OpenAI)...")
        self.llm = ChatOpenRouter(model="google/gemini-2.5-flash-lite", temperature=0.7)
        self.get_logger().info("Nodo Langchain inicializado y esperando prompts en /llm_prompt.")

    def prompt_callback(self, msg):
        prompt_text = msg.data
        self.get_logger().info(f"Recibido prompt: '{prompt_text}'")
        
        try:
            # 3. Procesar el prompt con Langchain
            messages = [HumanMessage(content=prompt_text)]
            response = self.llm.invoke(messages)
            
            # 4. Publicar la respuesta
            response_msg = String()
            response_msg.data = response.content
            self.publisher_.publish(response_msg)
            
            self.get_logger().info(f"Respuesta publicada: '{response.content[:50]}...'")
            
        except Exception as e:
            self.get_logger().error(f"Error procesando con Langchain: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = LangchainNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()