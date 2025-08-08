import cv2
import numpy as np

def get_main_contour(image_path: str):
    """
    Loads an image, isolates the red polygon, and returns its main contour.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image at {image_path}")
        return None

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 50])
    upper_red1 = np.array([10, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    lower_red2 = np.array([170, 100, 50])
    upper_red2 = np.array([180, 255, 255])
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"Warning: No contours found in {image_path}")
        return None
    return max(contours, key=cv2.contourArea)


def normalize_contour(contour):
    """
    Normalize contour by centering it and scaling to unit area.
    """
    # Calculate centroid
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return contour
    
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    
    # Center the contour
    centered_contour = contour.copy()
    centered_contour[:, 0, 0] -= cx
    centered_contour[:, 0, 1] -= cy
    
    # Scale to unit area
    area = cv2.contourArea(contour)
    if area > 0:
        scale = 1.0 / np.sqrt(area)
        centered_contour = (centered_contour * scale).astype(np.int32)
    
    return centered_contour


def transform_and_match(contour_a, contour_b):
    """
    Improved matching function with proper contour transformations and scale normalization.
    """
    # Normalize both contours for better comparison
    norm_contour_a = normalize_contour(contour_a)
    norm_contour_b = normalize_contour(contour_b)
    
    # Calculate centroids for rotation center
    M_a = cv2.moments(contour_a)
    M_b = cv2.moments(contour_b)
    
    if M_a["m00"] == 0 or M_b["m00"] == 0:
        return {'score': float('inf'), 'flip': 'None', 'rotation': 0}
    
    center_a = (int(M_a["m10"] / M_a["m00"]), int(M_a["m01"] / M_a["m00"]))
    center_b = (int(M_b["m10"] / M_b["m00"]), int(M_b["m01"] / M_b["m00"]))
    
    # Test both flip states and all rotations
    best_match = {'score': float('inf'), 'flip': 'None', 'rotation': 0}
    rotations = [0, 90, 180, 270]
    
    for flip_horizontal in [False, True]:
        # Create flipped version of contour_b if needed
        test_contour_b = contour_b.copy()
        if flip_horizontal:
            # Flip horizontally around the centroid
            test_contour_b[:, 0, 0] = center_b[0] - (test_contour_b[:, 0, 0] - center_b[0])
        
        # Normalize the test contour
        norm_test_contour_b = normalize_contour(test_contour_b)
        
        for angle in rotations:
            # Create rotation matrix around the centroid
            M = cv2.getRotationMatrix2D(center_b, angle, 1.0)
            
            # Apply rotation
            rotated_contour = cv2.transform(test_contour_b, M)
            
            # Normalize the rotated contour
            norm_rotated_contour = normalize_contour(rotated_contour)
            
            # Compare shapes using multiple methods for robustness
            score1 = cv2.matchShapes(norm_contour_a, norm_rotated_contour, cv2.CONTOURS_MATCH_I1, 0.0)
            score2 = cv2.matchShapes(norm_contour_a, norm_rotated_contour, cv2.CONTOURS_MATCH_I2, 0.0)
            score3 = cv2.matchShapes(norm_contour_a, norm_rotated_contour, cv2.CONTOURS_MATCH_I3, 0.0)
            
            # Use the best score among the three methods
            score = min(score1, score2, score3)
            
            if score < best_match['score']:
                best_match['score'] = score
                best_match['flip'] = 'Horizontal' if flip_horizontal else 'None'
                best_match['rotation'] = angle
    
    return best_match


def visualize_result(img_a_path, img_b_path, best_transform):
    """
    Creates a visual representation of the original and transformed shapes.
    """
    img_a = cv2.imread(img_a_path)
    img_b = cv2.imread(img_b_path)
    
    transformed_img_b = img_b.copy()
    (h_b, w_b) = transformed_img_b.shape[:2]
    center_b = (w_b / 2, h_b / 2)
    
    if best_transform['flip'] == 'Horizontal':
        transformed_img_b = cv2.flip(transformed_img_b, 1)

    angle = best_transform['rotation']
    if angle in [90, 270]:
        M = cv2.getRotationMatrix2D(center_b, angle, 1.0)
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h_b * sin) + (w_b * cos))
        new_h = int((h_b * cos) + (w_b * sin))
        M[0, 2] += (new_w / 2) - center_b[0]
        M[1, 2] += (new_h / 2) - center_b[1]
        transformed_img_b = cv2.warpAffine(transformed_img_b, M, (new_w, new_h))
    elif angle == 180:
        M = cv2.getRotationMatrix2D(center_b, angle, 1.0)
        transformed_img_b = cv2.warpAffine(transformed_img_b, M, (w_b, h_b))

    h_a, w_a = img_a.shape[:2]
    h_b_orig, w_b_orig = img_b.shape[:2]
    h_t, w_t = transformed_img_b.shape[:2]
    
    p_top = 60
    p_side = 20

    output_height = p_top + max(h_a, h_b_orig, h_t) + p_side
    output_width = p_side + w_a + p_side + w_b_orig + p_side + w_t + p_side
    
    result_img = np.full((output_height, output_width, 3), 255, dtype=np.uint8)

    x_pos = p_side
    result_img[p_top:p_top+h_a, x_pos:x_pos+w_a] = img_a
    cv2.putText(result_img, "Reference A", (x_pos, p_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    x_pos += w_a + p_side
    result_img[p_top:p_top+h_b_orig, x_pos:x_pos+w_b_orig] = img_b
    cv2.putText(result_img, "Original B", (x_pos, p_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    x_pos += w_b_orig + p_side
    result_img[p_top:p_top+h_t, x_pos:x_pos+w_t] = transformed_img_b
    cv2.putText(result_img, "Transformed B", (x_pos, p_top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    # cv2.imshow("Result", result_img)
    cv2.imwrite("result.png", result_img)
    # print("\nVisual result saved as 'result.png'. Press any key to exit.")
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


def debug_contour_matching(contour_a, contour_b, best_transform):
    """
    Debug function to visualize contour matching process.
    """
    # Create a blank canvas
    canvas_size = 800
    canvas = np.full((canvas_size, canvas_size, 3), 255, dtype=np.uint8)
    
    # Calculate centroids
    M_a = cv2.moments(contour_a)
    M_b = cv2.moments(contour_b)
    
    if M_a["m00"] == 0 or M_b["m00"] == 0:
        print("Error: Cannot calculate moments")
        return
    
    center_a = (int(M_a["m10"] / M_a["m00"]), int(M_a["m01"] / M_a["m00"]))
    center_b = (int(M_b["m10"] / M_b["m00"]), int(M_b["m01"] / M_b["m00"]))
    
    # Scale contours to fit canvas
    def scale_contour(contour, target_size=300):
        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)
        scale = min(target_size / max(w, h), 1.0)
        
        # Scale contour
        scaled_contour = contour.copy()
        scaled_contour = (scaled_contour * scale).astype(np.int32)
        
        # Center in canvas
        canvas_center = canvas_size // 2
        scaled_contour[:, 0, 0] += canvas_center - int(w * scale // 2)
        scaled_contour[:, 0, 1] += canvas_center - int(h * scale // 2)
        
        return scaled_contour
    
    # Draw original contours
    scaled_a = scale_contour(contour_a)
    scaled_b = scale_contour(contour_b)
    
    # Offset contour B to the right
    scaled_b[:, 0, 0] += canvas_size // 2
    
    # Draw contours
    cv2.drawContours(canvas, [scaled_a], -1, (0, 0, 255), 2)  # Red for reference
    cv2.drawContours(canvas, [scaled_b], -1, (255, 0, 0), 2)  # Blue for test
    
    # Add labels
    cv2.putText(canvas, "Reference A", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(canvas, "Original B", (canvas_size//2 + 50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # Apply transformation to contour B
    transformed_b = contour_b.copy()
    if best_transform['flip'] == 'Horizontal':
        transformed_b[:, 0, 0] = center_b[0] - (transformed_b[:, 0, 0] - center_b[0])
    
    if best_transform['rotation'] != 0:
        M = cv2.getRotationMatrix2D(center_b, best_transform['rotation'], 1.0)
        transformed_b = cv2.transform(transformed_b, M)
    
    # Scale and draw transformed contour
    scaled_transformed = scale_contour(transformed_b)
    scaled_transformed[:, 0, 0] += canvas_size // 2
    scaled_transformed[:, 0, 1] += canvas_size // 2  # Move down
    
    cv2.drawContours(canvas, [scaled_transformed], -1, (0, 255, 0), 2)  # Green for transformed
    cv2.putText(canvas, "Transformed B", (canvas_size//2 + 50, canvas_size//2 + 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Save debug image
    cv2.imwrite("debug_contours.png", canvas)
    print("Debug visualization saved as 'debug_contours.png'")


if __name__ == "__main__":
    # --- Make sure these file paths are correct ---
    IMAGE_A_PATH = "pydep/wld.png" 
    IMAGE_B_PATH = "pydep/pdf.png"

    print("Step 1: Processing Reference Image A...")
    contour_a = get_main_contour(IMAGE_A_PATH)

    print("Step 2: Processing Test Image B...")
    contour_b = get_main_contour(IMAGE_B_PATH)

    if contour_a is not None and contour_b is not None:
        print("\nStep 3: Finding the best transformation...")
        best_fit = transform_and_match(contour_a, contour_b)

        print("\n--- Match Found! ---")
        print(f"✅ Best Flip: {best_fit['flip']}")
        print(f"🔄 Best Rotation: {best_fit['rotation']} degrees")
        print(f"📏 Match Score: {best_fit['score']:.6f} (lower is better)")
        
        # Debug visualization
        debug_contour_matching(contour_a, contour_b, best_fit)
        
        visualize_result(IMAGE_A_PATH, IMAGE_B_PATH, best_fit)
    else:
        print("\nCould not complete matching due to errors in image processing.")