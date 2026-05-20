def to_grayscale(image, channel_order: str = "rgb"):
    """
    Convert an RGB/BGR image to grayscale manually using NumPy.

    The formula uses standard luminance weights. Pass `channel_order="bgr"`
    when the image came from OpenCV.
    """
    import numpy as np

    array = np.asarray(image, dtype="float32")
    if array.ndim == 2:
        return array.astype("uint8")
    if array.ndim != 3 or array.shape[2] < 3:
        raise ValueError("Expected a 2D grayscale or 3-channel color image.")

    if channel_order.lower() == "bgr":
        blue = array[:, :, 0]
        green = array[:, :, 1]
        red = array[:, :, 2]
    else:
        red = array[:, :, 0]
        green = array[:, :, 1]
        blue = array[:, :, 2]
    grayscale = 0.299 * red + 0.587 * green + 0.114 * blue
    return np.clip(grayscale, 0, 255).astype("uint8")


def convolve2d(image, kernel):
    """Apply a 2D convolution filter manually using NumPy."""
    import numpy as np

    image_array = np.asarray(image, dtype="float32")
    kernel_array = np.asarray(kernel, dtype="float32")

    if image_array.ndim != 2:
        raise ValueError("convolve2d expects a grayscale 2D image.")
    if kernel_array.ndim != 2:
        raise ValueError("Kernel must be 2D.")

    kernel_height, kernel_width = kernel_array.shape
    pad_y = kernel_height // 2
    pad_x = kernel_width // 2
    padded = np.pad(image_array, ((pad_y, pad_y), (pad_x, pad_x)), mode="edge")
    output = np.zeros_like(image_array, dtype="float32")

    flipped_kernel = np.flipud(np.fliplr(kernel_array))

    for y in range(image_array.shape[0]):
        for x in range(image_array.shape[1]):
            region = padded[y : y + kernel_height, x : x + kernel_width]
            output[y, x] = np.sum(region * flipped_kernel)

    return output


def sobel_edges(image, channel_order: str = "rgb"):
    """Run Sobel edge detection manually using NumPy convolution."""
    import numpy as np

    grayscale = to_grayscale(image, channel_order=channel_order)
    sobel_x = np.array(
        [
            [-1, 0, 1],
            [-2, 0, 2],
            [-1, 0, 1],
        ],
        dtype="float32",
    )
    sobel_y = np.array(
        [
            [-1, -2, -1],
            [0, 0, 0],
            [1, 2, 1],
        ],
        dtype="float32",
    )

    gradient_x = convolve2d(grayscale, sobel_x)
    gradient_y = convolve2d(grayscale, sobel_y)
    magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
    max_value = magnitude.max()
    if max_value > 0:
        magnitude = (magnitude / max_value) * 255

    return np.clip(magnitude, 0, 255).astype("uint8")
