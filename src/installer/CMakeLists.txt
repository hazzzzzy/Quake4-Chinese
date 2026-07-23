cmake_minimum_required(VERSION 3.20)
project(Quake4ChineseInstaller LANGUAGES CXX RC)

add_executable(q4cn_launcher WIN32
    launcher/main.cpp
    launcher/launcher.rc
)
target_compile_features(q4cn_launcher PRIVATE cxx_std_17)
target_compile_definitions(q4cn_launcher PRIVATE UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX)
target_compile_options(q4cn_launcher PRIVATE /utf-8 /W4 /WX)
target_link_options(q4cn_launcher PRIVATE /MANIFEST:NO)
target_link_libraries(q4cn_launcher PRIVATE shell32 ole32 uuid)
set_target_properties(q4cn_launcher PROPERTIES
    OUTPUT_NAME "Q4CNLauncher"
)
