import pytest
import rclpy

# En TDD estricto, este import fallará al principio.
# Debemos crear el archivo vacío mi_paquete_llm/tools/ros2_service_tool.py para solucionarlo.
from autonomous_rover_brain.tools.ros2_service_tool import ROS2ServiceTool
from rclpy.node import Node
from std_srvs.srv import (
    Trigger,  # Usamos Trigger como ejemplo; cámbialo por tu tipo de servicio
)


@pytest.fixture
def ros2_context():
    """
    Fixture para manejar el ciclo de vida de ROS2 de forma aislada.
    Inicia rclpy antes del test y lo apaga correctamente al finalizar.
    """
    rclpy.init()
    yield
    rclpy.shutdown()


@pytest.fixture
def mock_node(ros2_context):
    """
    Proporciona un nodo de ROS2 real para inyectar en la herramienta,
    pero sin interactuar con la red.
    """
    node = Node("test_service_tool_node")
    yield node
    node.destroy_node()


def test_tool_calls_ros2_service_successfully(mock_node, mocker):
    """
    Verifica que la herramienta Langchain invoque el servicio ROS2 correcto,
    maneje la respuesta simulada y devuelva el resultado en texto para el Agente.
    """
    # 1. PREPARACIÓN (Arrange)
    service_name = "/trigger_action"

    # Creamos un mock del cliente y su respuesta
    mock_client = mocker.MagicMock()
    mock_response = Trigger.Response()
    mock_response.success = True
    mock_response.message = "Acción completada vía ROS2."

    # Simulamos el comportamiento del cliente síncrono.
    # (Si usas call_async en producción, deberemos mockear el Future devuelto).
    mock_client.call.return_value = mock_response

    # Interceptamos la creación del cliente en nuestro nodo mock
    mocker.patch.object(mock_node, "create_client", return_value=mock_client)

    # Instanciamos la herramienta (comentado hasta que creemos la clase base)
    tool = ROS2ServiceTool(
        name="trigger_ros2_action",
        description="Llama a un servicio de ROS2 para ejecutar una acción.",
        node=mock_node,
        service_name=service_name,
    )

    # 2. ACCIÓN (Act)
    # Simulamos la llamada del Agente a la herramienta
    tool_input = "Inicia la secuencia"
    result = tool._run(tool_input)

    # 3. ASERCIÓN (Assert)
    # Aseguramos que la herramienta creó el cliente con el tipo de servicio y nombre correctos
    mock_node.create_client.assert_called_once_with(Trigger, service_name)

    # Aseguramos que el servicio fue llamado
    mock_client.call.assert_called_once()

    # Verificamos que la herramienta parseó la respuesta del servicio para dársela al LLM
    assert "Acción completada" in result
    assert result == "Success: Acción completada vía ROS2."


from autonomous_rover_brain.tools.ros2_service_tool import SetWheelVelocityTool

from robot_interfaces.srv import SetWheelVelocity


def test_set_wheel_velocity_tool_maps_arguments_correctly(mock_node, mocker):
    """
    Verifica que la herramienta extraiga los argumentos del LLM,
    los asigne al Request de ROS 2 y retorne la respuesta adecuadamente.
    """
    # 1. PREPARACIÓN
    service_name = "/motor/set_velocity"

    # Mock del cliente y la respuesta de ROS 2
    mock_client = mocker.MagicMock()
    mock_response = SetWheelVelocity.Response()
    mock_response.success = True
    mock_response.message = "Velocidad ajustada correctamente."
    mock_response.current_rpm = 50.5

    mock_client.call.return_value = mock_response
    mocker.patch.object(mock_node, "create_client", return_value=mock_client)

    tool = SetWheelVelocityTool(node=mock_node, service_name=service_name)

    # 2. ACCIÓN
    # En Langchain, el Agente pasaría los argumentos como un diccionario
    # gracias a nuestro esquema Pydantic.
    result = tool._run(wheel_id="front_left", rpm=50.5)

    # 3. ASERCIONES
    # Verificamos que se creó el cliente para el tipo de servicio correcto
    mock_node.create_client.assert_called_once_with(SetWheelVelocity, service_name)

    # Obtenemos el Request real que la herramienta intentó enviar
    mock_client.call.assert_called_once()
    called_request = mock_client.call.call_args[0][0]

    # ¡LA PRUEBA CLAVE! ¿Los datos del LLM se mapearon bien a ROS 2?
    assert called_request.wheel_id == "front_left"
    assert called_request.rpm == 50.5

    # Verificamos la respuesta formateada para el LLM
    assert "Velocidad ajustada" in result
    assert "50.5" in result

from robot_interfaces.srv import SetWheelPosition
from autonomous_rover_brain.tools.ros2_service_tool import SetWheelPositionTool

def test_set_wheel_position_tool_maps_arguments_correctly(mock_node, mocker):
    """Verifica el envío de un string y un float a un servicio."""
    service_name = "/motor/set_position"
    
    # 1. Arrange
    mock_client = mocker.MagicMock()
    mock_response = SetWheelPosition.Response()
    mock_response.success = True
    mock_response.message = "Posición alcanzada."
    mock_response.final_position_deg = 90.0
    
    mock_client.call.return_value = mock_response
    mocker.patch.object(mock_node, 'create_client', return_value=mock_client)

    tool = SetWheelPositionTool(node=mock_node, service_name=service_name)

    # 2. Act
    result = tool._run(wheel_id="rear_right", position_deg=90.0)

    # 3. Assert
    mock_node.create_client.assert_called_once_with(SetWheelPosition, service_name)
    mock_client.call.assert_called_once()
    
    called_request = mock_client.call.call_args[0][0]
    assert called_request.wheel_id == "rear_right"
    assert called_request.position_deg == 90.0
    
    # El LLM necesita saber en qué posición quedó realmente
    assert "90.0" in result