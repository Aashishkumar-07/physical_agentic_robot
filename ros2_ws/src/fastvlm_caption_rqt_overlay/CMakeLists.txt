cmake_minimum_required(VERSION 3.8)
project(fastvlm_caption_rqt_overlay)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_ros REQUIRED)
find_package(rqt_image_overlay_layer REQUIRED)
find_package(std_msgs REQUIRED)

add_library(caption_layer src/caption_layer.cpp)
add_library(fastvlm_caption_rqt_overlay::caption_layer ALIAS caption_layer)
target_compile_features(caption_layer PUBLIC c_std_99 cxx_std_17)  # Require C99 and C++17
target_include_directories(caption_layer PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/${PROJECT_NAME}>)
ament_target_dependencies(
  caption_layer
  "rqt_image_overlay_layer"
  "std_msgs"
)

pluginlib_export_plugin_description_file(rqt_image_overlay_layer plugins.xml)

# Causes the visibility macros to use dllexport rather than dllimport,
# which is appropriate when building the dll but not consuming it.
target_compile_definitions(caption_layer PRIVATE "FASTVLM_CAPTION_RQT_OVERLAY_BUILDING_LIBRARY")

install(
  DIRECTORY include/
  DESTINATION include/${PROJECT_NAME}
)
install(
  TARGETS caption_layer
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_include_directories(
  "include/${PROJECT_NAME}"
)
ament_export_libraries(
  caption_layer
)
ament_export_targets(
  export_${PROJECT_NAME}
)

ament_package()
