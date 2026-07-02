![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_Noble-E95420?logo=ubuntu)
![ROS2](https://img.shields.io/badge/ROS2-Jazzy_Jalisco-22314E?logo=ros)
![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-0F5C9F?logo=gazebo&logoColor=white)
![FastVLM](https://img.shields.io/badge/FastVLM-Vision_Language_Model-teal)
![DepthAnything](https://img.shields.io/badge/DepthAnything3-Monocular_Depth-brown)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Workflows-purple)
![LLM](https://img.shields.io/badge/LLM-Qwen3:8B-blue)
![CLIP](https://img.shields.io/badge/CLIP-Multimodal_Embedding-red)
![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-darkred)
![FastAPI](https://img.shields.io/badge/FastAPI-REST_API-009688?logo=fastapi)
![](https://badge.mcpx.dev "MCP")
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Message%20Broker-FF6600?logo=rabbitmq)
![Supabase](https://img.shields.io/badge/Supabase-File_Storage-3ECF8E?logo=supabase)


### Overview 
A robotics and AI project exploring how autonomous agents can perceive, remember, reason and act inside physical environments using ROS2, AI models, semantic vector memory and agentic planning workflows.

### Physical Agent Robot Demo
https://github.com/user-attachments/assets/975c9b2d-d9b8-412c-bbc5-55d7926b06d1

### High Level Architecture 

<img width="662" height="499" alt="image" src="https://github.com/user-attachments/assets/b29e40fa-c280-476f-8c27-ce1c83e096ab" />

<br>

---

<img width="1062" height="683" alt="image" src="https://github.com/user-attachments/assets/439ca75e-e26e-4ff0-9a6d-82b0669b0ea4" />


<br>

---

<img width="1211" height="417" alt="image" src="https://github.com/user-attachments/assets/d0a0dcd1-dd3b-467c-b5e4-2b38de972934" />

### LangGraph Workflow
<img width="216" height="249" alt="langgraph" src="https://github.com/user-attachments/assets/80c5a446-4e14-4780-9880-2727e8ac5546" />

<br>

### Repository Packages Overview

| 📦ROS2 Package/📂Folder | Description |
|--------------|-------------|
| 📦 `aws-robomaker-small-warehouse-world` <br>*(submodule)* | **Simulation Environment**<br>• AWS RoboMaker small warehouse is used as the Gazebo world in which the robot is launched and tested. |
| 📦  `Depth-Anything-3-ROS2` <br>*(submodule)* | **Depth Estimation Layer**<br>• Performs monocular depth estimation from RGB camera input without requiring dedicated depth sensors.<br>• Raw depth output is consumed by `vision_spatial_mapping`.<br>• Normalized depth maps are consumed by Rviz for better visualization.|
| 📦 `my_robot_description` |**Robot Description & Kinematics** <br>• Unified robot description format is an XML format file used to describe  robot’s physical/geometry & visual features(links & joints).<br>• Used for generating  kinematic model (TF frames) <br>• Used for describing sensor (camera, LiDAR) & actuator (diff-drive, joint state publisher) placement. |
| 📦 `my_robot_bringup` | **Configuration & Launch files** <br>• It contains the configuration for Rviz, Nav2, gazebo_ros_bridge.<br>• RViz is used for 3D visualization of robot model & TF verification. <br>• Gazebo bridge package provides a network bridge, which enables the exchange of messages between ROS & Gazebo Transport.<br>• Launch files for ROS2 nodes (RViz, gz-sim, DA3, etc.) |
| 📦 `my_robot_interfaces` |**Custom Interfaces** <br>•  Custom ROS2 message and service interface definitions. |
| 📦 `fastvlm_caption_rqt_overlay` | **Real-Time Caption Visualization**<br>• RQT plugin overlaying FastVLM-generated captions on live camera images for real-time visualization. |
| 📦 `vision_spatial_mapping` | **Spatial Mapping Pipeline**<br>• Receives camera frames, DA3 depth output and TF transforms.<br>• Extracts depth from the central pixel region to estimate 3D coordinates in the map frame.<br> • The camera field-of-view is intentionally narrowed to reduce spatial estimation error introduced by central-region depth approximation. <br>• Uploads the image to Supabase File Storage and publishes the image reference and spatial coordinates to the RabbitMQ message broker. |
| 📂 `image_caption_publisher` | **Live captioning** <br>• Sends a HTTP/2 request with a configurable timeout, containing image bytes to the backend server. <br>• The captioning loop runs at 2 Hz. Only one caption request is allowed at a time, preventing multiple pending requests from accumulating. Each new request uses the latest available image frame. As a tradeoff, some intermediate scenes may be skipped if caption generation takes longer than the request interval. |
| 📂`robot_agent` | **Agentic Planning Layer**<br>• Implements the core planning, reasoning and tool orchestration loop using LangGraph. The AI agent is powered by a locally running Qwen3.5:9B model.<br>• Uses dedicated prompts and subgraphs with isolated state to enable context engineering, preventing the main agent's context from being bloated with intermediate search results |  

### Related Services

| Service | Purpose |
|---|---|
| [`clip_faiss_server`](https://github.com/Aashishkumar-07/clip-faiss-server) | **Visual-Spatial Semantic Memory Backend**<br>• [**v1.0.0**](https://github.com/Aashishkumar-07/clip-faiss-server/releases#:~:text=faiss%2Dserver%20v1.0.0-,clip%2Dfaiss%2Dserver%20v1.0.0,-Compare) →  `Uvicorn` ASGI Server + `FastAPI` Backend Framework for automatic generation of interactive `OpenAPI/Swagger UI documentation`  + `CLIP` for multimodal embedding generation + `FAISS` for vector storage and semantic retrieval (IndexFlatIP, cosine similarity) through REST APIs + `Pydantic` for providing schema validation.<br>• [**v2.0.0**](https://github.com/Aashishkumar-07/clip-faiss-server/releases#:~:text=faiss%2Dserver%20v2.0.0-,clip%2Dfaiss%2Dserver%20v2.0.0,-Latest) → Supports asynchronous event-driven image ingestion via `RabbitMQ` using MQTT plugin + server-side `FastVLM` captioning only for semantically distinct scenes + claim-check pattern using `Supabase` File Storage to support large image payloads (>1MB) |
| [`physical_robot_agent_mcp_server`](https://github.com/Aashishkumar-07/physical_robot_agent_mcp_server) | **Extended Nav2 MCP Server**<br>Extends the Nav2 MCP server by integrating a FAISS-based semantic search tool for agent memory retrieval, transforming navigation into a memory-augmented autonomous agent system. |



### Setup 
Setup and installation instructions are currently being documented.
