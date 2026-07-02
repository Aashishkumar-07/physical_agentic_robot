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

### Overview 
A robotics and AI project exploring how autonomous agents can perceive, remember, reason and act inside physical environments using ROS2, AI models, semantic vector memory and agentic planning workflows.

### Physical Agent Robot Demo
https://github.com/user-attachments/assets/975c9b2d-d9b8-412c-bbc5-55d7926b06d1

### High Level Architecture 
<img width="1341" height="394" alt="image" src="https://github.com/user-attachments/assets/95d25f48-aedf-44bc-a387-1ec4f9e697c3" />

### LangGraph Workflow
<img width="216" height="249" alt="langgraph" src="https://github.com/user-attachments/assets/80c5a446-4e14-4780-9880-2727e8ac5546" />

<br>

### Repository Packages Overview

| 📦Package/📄File | Description |
|--------------|-------------|
| 📦 `aws-robomaker-small-warehouse-world` <br>*(submodule)* | **Simulation Environment**<br>• AWS RoboMaker small warehouse is used as the Gazebo world in which the robot is launched and tested. |
| 📦  `Depth-Anything-3-ROS2` <br>*(submodule)* | **Depth Estimation Layer**<br>• Performs monocular depth estimation from RGB camera input without requiring dedicated depth sensors.<br>• Raw depth output is consumed by `vision_spatial_mapping`.<br>• Normalized depth maps are consumed by Rviz for better visualization.|
| 📦 `fastvlm_ros` <br>*(submodule)* | **Vision-Language Understanding**<br>• Uses FastVLM to generate scene captions from image frames.<br>• Captions are used for real-time scene understanding & are also stored as metadata alongside image embeddings in FAISS for semantic retrieval. |
| 📦 `my_robot_description` |**Robot Description & Kinematics** <br>• Unified robot description format is an XML format file used to describe  robot’s physical/geometry & visual features(links & joints).<br>• Used for generating  kinematic model (TF frames) <br>• Used for describing sensor (camera, LiDAR) & actuator (diff-drive, joint state publisher) placement. |
| 📦 `my_robot_bringup` | **Configuration & Launch files** <br>• It contains the configuration for Rviz, Nav2, gazebo_ros_bridge.<br>• RViz is used for 3D visualization of robot model & TF verification. <br>• Gazebo bridge package provides a network bridge, which enables the exchange of messages between ROS & Gazebo Transport.<br>• Launch files for ROS2 nodes (RViz, gz-sim, DA3, etc.) |
| 📦 `my_robot_interfaces` |**Custom Interfaces** <br>•  Custom ROS2 message and service interface definitions. |
| 📦 `fastvlm_caption_rqt_overlay` | **Real-Time Caption Visualization**<br>• RQT plugin overlaying FastVLM-generated captions on live camera images for real-time visualization. |
| 📦 `vision_spatial_mapping` | **Spatial Mapping Pipeline**<br>• Receives camera frames, DA3 depth output and TF transforms.<br>• Extracts depth from the central pixel region to estimate 3D coordinates in the map frame.<br> • The camera field-of-view is intentionally narrowed to reduce spatial estimation error introduced by central-region depth approximation. <br>• Makes a service call to `fastvlm_ros` for scene caption generation.<br>• Sends an HTTP request to `clip_faiss_server` with the image, caption, and coordinates in the request body.<br>• Stores image embeddings in FAISS, while caption, coordinates, and image filename are stored as metadata.<br>• Generates searchable semantic memory entries associated with map-frame 3D coordinates. |
|📄 `robot_agent.py` | **Agentic Planning Layer**<br>• The core planner-tool reasoning and decision loop is implemented using LangGraph. The AI agent is powered by running locally Qwen3:8B LLM model with LangChain MCP Client.| 

### Related Services

| Service | Purpose |
|---|---|
| [`clip_faiss_server`](https://github.com/Aashishkumar-07/clip-faiss-server) | **Semantic Memory Backend**<br>Uvicorn ASGI Server + FastAPI + CLIP + FAISS + Pydantic for multimodal embedding generation, vector storage and semantic retrieval (FlatIndexIP, cosine similarity) through REST APIs. Provides schema validation, automatic interactive API documentation and long-term memory-augmented reasoning capabilities. |
| [`physical_robot_agent_mcp_server`](https://github.com/Aashishkumar-07/physical_robot_agent_mcp_server) | **Extended Nav2 MCP Server**<br>Extends the Nav2 MCP server by integrating a FAISS-based semantic search tool for agent memory retrieval, transforming navigation into a memory-augmented autonomous agent system. |



### Setup 
Setup and installation instructions are currently being documented.
