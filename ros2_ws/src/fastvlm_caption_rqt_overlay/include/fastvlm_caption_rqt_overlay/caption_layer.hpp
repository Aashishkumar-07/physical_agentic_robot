#ifndef FASTVLM_CAPTION_RQT_OVERLAY__CAPTION_LAYER_HPP_
#define FASTVLM_CAPTION_RQT_OVERLAY__CAPTION_LAYER_HPP_

#include "fastvlm_caption_rqt_overlay/visibility_control.h"
#include "rqt_image_overlay_layer/plugin.hpp"
#include "std_msgs/msg/string.hpp"

namespace fastvlm_caption_rqt_overlay
{

class CaptionLayer: public rqt_image_overlay_layer::Plugin<std_msgs::msg::String> 
{
protected:
  void overlay(QPainter & painter, const std_msgs::msg::String & msg) override;
};

}  // namespace fastvlm_caption_rqt_overlay

#endif  // FASTVLM_CAPTION_RQT_OVERLAY__CAPTION_LAYER_HPP_
