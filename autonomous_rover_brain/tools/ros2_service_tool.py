from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from std_srvs.srv import Trigger

from robot_interfaces.srv import SetWheelVelocity, SetWheelPosition


class ROS2ServiceTool(BaseTool):
    name: str = "ros2_service_tool"
    description: str = "Una herramienta base para llamar servicios de ROS2"

    node: Any = Field(exclude=True)  # Evita que Langchain intente parsear el Nodo
    service_name: str

    def _run(self, tool_input: str) -> str:
        """La lógica sincrónica que ejecuta el Agente de Langchain."""

        client = self.node.create_client(Trigger, self.service_name)

        request = Trigger.Request()

        response = client.call(request)

        if response.success:
            return f"Success: {response.message}"
        else:
            return f"Failed: {response.message}"

    async def _arun(self, tool_input: str) -> str:
        """Obligatorio implementar en BaseTool, aunque no lo usemos por ahora."""
        raise NotImplementedError("Esta herramienta no soporta asincronía aún.")


class SetWheelVelocitySchema(BaseModel):
    """Esquema que el LLM leerá para saber qué datos enviar."""

    wheel_id: str = Field(
        ...,  # Los tres puntos indican que es un campo obligatorio
        description="Identificador de la rueda (ej: 'front_left', 'front_right', 'rear_left', 'rear_right').",
    )
    rpm: float = Field(
        ...,
        description="Velocidad deseada en Revoluciones Por Minuto (RPM). Un número negativo invierte el giro.",
    )


class SetWheelPositionSchema(BaseModel):
    wheel_id: str = Field(
        ...,
        description="Identificador de la rueda (ej: 'front_left', 'front_right', 'rear_left', 'rear_right').",
    )
    position_deg: float = Field(..., description="Posicion deseada en grados (0-360)")


class SetWheelVelocityTool(BaseTool):
    name: str = "set_wheel_velocity"
    description: str = (
        "Ajusta la velocidad de rotación (RPM) de una rueda específica del rover."
    )

    args_schema: Type[BaseModel] = SetWheelVelocitySchema

    node: Any = Field(exclude=True)
    service_name: str = "/set_wheel_velocity"  # Topic por defecto

    def _run(self, wheel_id: str, rpm: float) -> str:

        client = self.node.create_client(SetWheelVelocity, self.service_name)

        request = SetWheelVelocity.Request()
        request.wheel_id = wheel_id
        request.rpm = float(rpm)  # Aseguramos el casteo a float

        response = client.call(request)

        if response.success:
            return f"Éxito: {response.message}. RPM actual: {response.current_rpm}"
        else:
            return f"Fallo al ajustar velocidad: {response.message}"

    async def _arun(self, *args, **kwargs) -> str:
        raise NotImplementedError("La herramienta no soporta asincronía aún.")


class SetWheelPositionTool(BaseTool):
    name: str = "set_wheel_position"
    description: str = "Ajusta la posicion angular de una rueda específica del rover."

    args_schema: Type[BaseModel] = SetWheelPositionSchema

    node: Any = Field(exclude=True)
    service_name: str = "/set_wheel_position"  # Topic por defecto

    def _run(self, wheel_id: str, position_deg: float) -> str:

        # client = self.node.create_client(SetWheelPosition, self.service_name)

        # request = SetWheelPosition.Request()
        # request.wheel_id = wheel_id
        # request.position_deg = float(position_deg)  # Aseguramos el casteo a float

        # response = client.call(request)

        # if response.success:
        #     return f"Éxito: {response.message}. Posicion angular actual: {response.current_rpm}"
        # else:
        #     return f"Fallo al ajustar la posicion: {response.message}"

        print(f"wheel_id:{wheel_id}, position_deg:{position_deg}")

    async def _arun(self, *args, **kwargs) -> str:
        raise NotImplementedError("La herramienta no soporta asincronía aún.")
