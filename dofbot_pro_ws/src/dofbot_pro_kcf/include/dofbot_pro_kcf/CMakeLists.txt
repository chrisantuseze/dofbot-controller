FILE(GLOB_RECURSE SOURCEFILES "*.cpp" "*.h")
# Exclude Jupyter checkpoint files from the source list
foreach(_f ${SOURCEFILES})
	if(_f MATCHES "\\.ipynb_checkpoints")
		list(REMOVE_ITEM SOURCEFILES ${_f})
	endif()
endforeach()
add_library(kcftracker ${SOURCEFILES})
target_link_libraries(kcftracker ${catkin_LIBRARIES})
