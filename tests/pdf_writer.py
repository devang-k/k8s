from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import os

class PDFWriter:
    def __init__(self, title: str, path: str, date: str):
        """
        Initialize the PDFWriter with a title, save path, and creation date.

        Args:
            title (str): Title of the PDF document.
            path (str): Path where the PDF will be saved.
            date (str): Date of creation in string format (e.g., 'YYYY-MM-DD').
        """
        self.title = title
        self.path = path
        self.date = date
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.pdf.add_page()
        self.pdf.set_font("helvetica", size=12)
        self.pdf.set_title(title)
        self._write_metadata()

    def _write_metadata(self):
        """
        Write metadata such as title and date on the first page of the PDF.
        """
        self.pdf.set_font("helvetica", style="B", size=16)
        self.pdf.cell(0, 10, self.title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.pdf.ln(10)
        self.pdf.set_font("helvetica", size=12)
        self.pdf.cell(0, 10, f"Date: {self.date}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.pdf.ln(20)

    def append(self, type: str, data):
        """
        Append content to the PDF.

        Args:
            type (str): The type of content ("text" or "images").
            data: 
                - If type is "text": A string to append as text.
                - If type is "images": A dictionary where keys are labels for images and values are image paths.
        """
        if type == "text":
            if isinstance(data, str):
                # Append text to the PDF
                self.pdf.multi_cell(0, 10, data)
                self.pdf.ln(5)
            else:
                raise ValueError("For type 'text', data must be a string.")
        
        elif type == "images":
            if isinstance(data, dict):
                # Append images to the PDF
                images = list(data.items())  # Convert dictionary to a list of (label, path) tuples
                image_height = 60  # Fixed height for each image
                
                for i in range(0, len(images), 2):  # Process two images per row
                    self.pdf.ln(10)
                    y_start = self.pdf.get_y()  # Get current y position
                    x_start = 10  # Start position for images (left margin)
                    
                    row_images = images[i:i+2]  # Get the current set of two images
                    for label, path in row_images:
                        if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg')):
                            image_width = (self.pdf.w - 30) / 2  # Calculate image width for two per row
                            x_pos = x_start
                            
                            # Add the label
                            self.pdf.set_xy(x_pos, y_start)
                            self.pdf.set_font("helvetica", size=10)
                            self.pdf.cell(image_width, 5, label, align="C")
                            
                            # Add the image below the label
                            self.pdf.image(path, x=x_pos, y=y_start + 5, w=image_width, h=image_height)
                            
                            # Update x_start for the next image in the row
                            x_start += image_width + 10
                        else:
                            raise ValueError(f"Invalid image path: {path}")
                    
                    # Adjust y_start for the next row
                    self.pdf.set_y(y_start + image_height + 15)  # Image height + margin
                self.pdf.add_page()
            else:
                raise ValueError("For type 'images', data must be a dictionary with labels as keys and paths as values.")
        
        else:
            raise ValueError("Invalid type. Use 'text' or 'images'.")

    def save(self):
        """
        Save the PDF to the specified path.
        """
        try:
            self.pdf.output(self.path)
            print(f"PDF saved successfully to {self.path}")
        except Exception as e:
            print(f"Failed to save PDF: {e}")

# Example Usage:
if __name__ == "__main__":
    pdf_writer = PDFWriter(title="My PDF Title", path="sample.pdf", date=datetime.now().strftime("%Y-%m-%d"))
    pdf_writer.append("text", "This is some text in the PDF.")
    pdf_writer.append("images", {
        "generated": "wrong_cells/AOI21X1_1_RT_6_generated.png",
        "golden data": "wrong_cells/AOI21X1_1_RT_6_orig.png",
        "difference": "wrong_cells/AOI21X1_1_RT_6.png"
    })
    pdf_writer.append("text", "This is some text in the PDF.")
    pdf_writer.save()