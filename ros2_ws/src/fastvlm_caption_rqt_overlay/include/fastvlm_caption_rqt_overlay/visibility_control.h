#ifndef FASTVLM_CAPTION_RQT_OVERLAY__VISIBILITY_CONTROL_H_
#define FASTVLM_CAPTION_RQT_OVERLAY__VISIBILITY_CONTROL_H_

// This logic was borrowed (then namespaced) from the examples on the gcc wiki:
//     https://gcc.gnu.org/wiki/Visibility

#if defined _WIN32 || defined __CYGWIN__
  #ifdef __GNUC__
    #define FASTVLM_CAPTION_RQT_OVERLAY_EXPORT __attribute__ ((dllexport))
    #define FASTVLM_CAPTION_RQT_OVERLAY_IMPORT __attribute__ ((dllimport))
  #else
    #define FASTVLM_CAPTION_RQT_OVERLAY_EXPORT __declspec(dllexport)
    #define FASTVLM_CAPTION_RQT_OVERLAY_IMPORT __declspec(dllimport)
  #endif
  #ifdef FASTVLM_CAPTION_RQT_OVERLAY_BUILDING_LIBRARY
    #define FASTVLM_CAPTION_RQT_OVERLAY_PUBLIC FASTVLM_CAPTION_RQT_OVERLAY_EXPORT
  #else
    #define FASTVLM_CAPTION_RQT_OVERLAY_PUBLIC FASTVLM_CAPTION_RQT_OVERLAY_IMPORT
  #endif
  #define FASTVLM_CAPTION_RQT_OVERLAY_PUBLIC_TYPE FASTVLM_CAPTION_RQT_OVERLAY_PUBLIC
  #define FASTVLM_CAPTION_RQT_OVERLAY_LOCAL
#else
  #define FASTVLM_CAPTION_RQT_OVERLAY_EXPORT __attribute__ ((visibility("default")))
  #define FASTVLM_CAPTION_RQT_OVERLAY_IMPORT
  #if __GNUC__ >= 4
    #define FASTVLM_CAPTION_RQT_OVERLAY_PUBLIC __attribute__ ((visibility("default")))
    #define FASTVLM_CAPTION_RQT_OVERLAY_LOCAL  __attribute__ ((visibility("hidden")))
  #else
    #define FASTVLM_CAPTION_RQT_OVERLAY_PUBLIC
    #define FASTVLM_CAPTION_RQT_OVERLAY_LOCAL
  #endif
  #define FASTVLM_CAPTION_RQT_OVERLAY_PUBLIC_TYPE
#endif

#endif  // FASTVLM_CAPTION_RQT_OVERLAY__VISIBILITY_CONTROL_H_
