#include <QPainter>
#include <QFontMetrics>
#include "fastvlm_caption_rqt_overlay/caption_layer.hpp"

namespace fastvlm_caption_rqt_overlay
{
    void CaptionLayer::overlay(QPainter & painter, const std_msgs::msg::String & msg) {
        if (msg.data.empty()) return;

        QRect viewport = painter.viewport();
        int margin = 10;
        int available_width = viewport.width() - 2 * margin;

        QFont font("Arial", 12, QFont::Bold);
        painter.setFont(font);

        // Calculate exact bounding rect for wrapped text (prevents missing words/clipping)
        QRect dummy_rect(0, 0, available_width, 0);
        QRect needed_rect = painter.fontMetrics().boundingRect(
            dummy_rect, 
            Qt::AlignLeft | Qt::TextWordWrap, 
            QString::fromStdString(msg.data)
        );

        int text_padding = 15;
        int box_height = needed_rect.height() + 2 * text_padding + 15;  
        // Position at bottom
        QRect text_rect(margin, viewport.height() - box_height - margin, 
                        available_width, box_height);

        // Semi-transparent black background
        painter.setBrush(QColor(0, 0, 0, 180));
        painter.setPen(Qt::NoPen);
        painter.drawRoundedRect(text_rect, 10, 10);

        // Draw wrapped text (matches calculation flags for no clipping)
        painter.setPen(Qt::white);
        painter.drawText(
            text_rect.adjusted(text_padding, text_padding, -text_padding, -text_padding),
            Qt::AlignLeft | Qt::AlignTop | Qt::TextWordWrap,
            QString::fromStdString(msg.data)
        );

    }

}  // namespace fastvlm_caption_rqt_overlay

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(fastvlm_caption_rqt_overlay::CaptionLayer, rqt_image_overlay_layer::PluginInterface)
