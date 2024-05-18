from img_proc import Img

class Filters:
    def __init__(self, photo_caption, img_path):
        self.photo_caption = photo_caption
        self.img_path = img_path

    def image_processing(self):
        if 'blur' in self.photo_caption:
            return self.apply_blur_filter()
        elif 'contour' in self.photo_caption:
            return self.apply_contour_filter()
        elif 'rotate' in self.photo_caption:
            return self.apply_rotate_filter()
        elif 'salt and pepper' in self.photo_caption:
            return self.apply_salt_n_pepper_filter()
        elif 'segment' in self.photo_caption:
            return self.apply_segment_filter()
        elif 'random color' in self.photo_caption:
            return self.apply_random_colors_filter()
        else:
            return None, "No valid filter found"

    def apply_blur_filter(self):
        return self.apply_filter(Img.blur, 'Blur')

    def apply_contour_filter(self):
        return self.apply_filter(Img.contour, 'Contour')

    def apply_rotate_filter(self):
        return self.apply_filter(Img.rotate, 'Rotate')

    def apply_salt_n_pepper_filter(self):
        return self.apply_filter(Img.salt_n_pepper, 'Salt and Pepper')

    def apply_segment_filter(self):
        return self.apply_filter(Img.segment, 'Segment')

    def apply_random_colors_filter(self):
        return self.apply_filter(Img.random_colors, 'Random Colors')

    def apply_filter(self, filter_func, filter_name):
        img_instance = Img(self.img_path)
        filter_func(img_instance)  # Call the provided filter function
        processed_img_path = img_instance.save_img()

        return processed_img_path, filter_name
