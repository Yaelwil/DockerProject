from pathlib import Path
from matplotlib.image import imread, imsave
import math
import random


def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()
        self.info = self.calculate_image_info()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def calculate_image_info(self):
        """
        Calculate image dimensions and center.

        Returns:
            dict: Dictionary containing 'width', 'height', 'center_x', and 'center_y'.
        """
        width = len(self.data[0])
        height = len(self.data)

        if self.data[0][0] < 1:
            center_x = (width - 1) / 2
            center_y = (height - 1) / 2
        else:
            center_x = width / 2
            center_y = height / 2

        return {
            'width': width,
            'height': height,
            'center_x': center_x,
            'center_y': center_y
        }

    def blur(self, blur_level=16):

        image_info = self.calculate_image_info()
        width = image_info['width']
        height = image_info['height']
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j - 1] - row[j]))

            self.data[i] = res

    def rotate(self):
        """
        Rotate the image by 90 degrees.

        Returns:
            Img: Rotated image object.
        """
        # 1. Import the data from the basic_calculations function
        image_info = self.calculate_image_info()
        width = image_info['width']
        height = image_info['height']
        center_x = image_info['center_x']
        center_y = image_info['center_y']
        degrees = 90

        # 2. Calculate degrees in radiants
        radians = math.radians(degrees)

        # 3. Create new variable to store the new rotated image
        rotated_image = [[0] * width for _ in range(height)]

        # 4. Iterate over each pixel in the original image
        for y in range(height):
            for x in range(width):

                # 5. Calculate for each pixel its new location
                new_x = int((x - center_x) * math.cos(radians) - (y - center_y) * math.sin(radians) + center_x)
                new_y = int((x - center_x) * math.sin(radians) + (y - center_y) * math.cos(radians) + center_y)

                # 6. Check if new coordinates are within bounds
                if 0 <= new_x < width and 0 <= new_y < height:
                    # 7. Copy the pixel value to the rotated position
                    rotated_image[y][x] = self.data[new_y][new_x]

        # 8. Set the rotated data back to the instance
        self.data = rotated_image

        # 9. Display Result (optional, you might not want to return anything)
        return self

    def salt_n_pepper(self, salt_prob=0.02, pepper_prob=0.02):
        """
        Add salt-and-pepper noise to the image.

        Args:
            salt_prob (float): Probability of adding salt noise.
            pepper_prob (float): Probability of adding pepper noise.
        """
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                rand = random.random()
                if rand < salt_prob:
                    self.data[i][j] = 255  # White pixel for salt noise
                elif rand > (1 - pepper_prob):
                    self.data[i][j] = 0  # Black pixel for pepper noise

    def concat(self, other_img, direction='horizontal'):
        """
        Concatenate the current image with another image.

        Args:
            other_img (Img): Another Image object to concatenate.
            direction (str): Concatenation direction, either 'horizontal' or 'vertical'.

        Returns:
            Img: Concatenated image object.
        """
        # Get the data of the other image
        other_data = other_img.data

        # Calculate the image information for the current instance
        self_info = self.calculate_image_info()
        self_height = self_info['height']
        self_width = self_info['width']

        # Calculate the image information for the other image
        other_info = other_img.calculate_image_info()
        other_height = other_info['height']
        other_width = other_info['width']

        # Verify the dimensions based on the concatenation direction
        if direction == 'horizontal':
            if self_height != other_height:
                raise RuntimeError(
                    "Image dimensions are not compatible for horizontal concatenation. Heights must be the same.")
            else:
                self.data = [row_self + row_other for row_self, row_other in zip(self.data, other_data)]
        elif direction == 'vertical':
            if self_width != other_width:
                raise RuntimeError(
                    "Image dimensions are not compatible for vertical concatenation. Widths must be the same.")
            else:
                self.data += other_data
        else:
            raise ValueError("Invalid concatenation direction. Use 'horizontal' or 'vertical'.")

        # Return a new Img instance with the concatenated data
        return Img(self.data)

    def segment(self):
        """
        Segment images (black and white).

        Returns:
            list: 2D list representing the segmented image.
        """

        # 1. Import the data from the basic_calculations function
        image_info = self.calculate_image_info()
        width = image_info['width']
        height = image_info['height']

        # 2. Create a new variable
        segmented_image = [[0] * width for _ in range(height)]

        # 3. Iterate over pixels
        for row in range(height):
            for col in range(width):
                pixel_intensity = self.data[row][col]

                # 4. Perform segmentation logic based on pixel intensity
                if pixel_intensity > 100:
                    # Replace pixel with white (intensity 255)
                    segmented_image[row][col] = 255

        self.data = segmented_image
        return segmented_image

    def rotate_by_degree(self, degrees):
        """
        Rotate the image by the specified degrees.

        Args:
            degrees (float): Rotation angle in degrees.

        Returns:
            Img: Rotated image object.
        """
        # 1. Import the data from the basic_calculations function
        image_info = self.calculate_image_info()
        width = image_info['width']
        height = image_info['height']
        center_x = image_info['center_x']
        center_y = image_info['center_y']

        # 2. Calculate degrees in radiants
        radians = math.radians(degrees)

        # 3. Create new variable to store the new rotated image
        rotated_image = [[0] * width for _ in range(height)]

        # 4. Iterate over each pixel in the original image
        for y in range(height):
            for x in range(width):

                # 5. Calculate for each pixel its new location
                new_x = int((x - center_x) * math.cos(radians) - (y - center_y) * math.sin(radians) + center_x)
                new_y = int((x - center_x) * math.sin(radians) + (y - center_y) * math.cos(radians) + center_y)

                # 6. Check if new coordinates are within bounds
                if 0 <= new_x < width and 0 <= new_y < height:
                    # 7. Copy the pixel value to the rotated position
                    rotated_image[y][x] = self.data[new_y][new_x]

        # 8. Set the rotated data back to the instance
        self.data = rotated_image

        # 9. Display Result (optional, you might not want to return anything)
        return self

    def random_colors(self):
        """
        Apply the 'random colors' filter to the image.
        Assigns a random RGB color to each pixel.
        """

        # Calculate the image information for the current instance
        self_info = self.calculate_image_info()
        height = self_info['height']
        width = self_info['width']

        for i in range(height):
            for j in range(width):
                # Generate random RGB values
                color = random.randint(0, 255)

                # Set the pixel color
                self.data[i][j] = color
