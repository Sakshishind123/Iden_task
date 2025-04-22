import json
import os
import asyncio
import time
import threading
import http.server
import socketserver
from pathlib import Path
from playwright.async_api import async_playwright, Page, TimeoutError

# Create a directory for our local server files
os.makedirs("local_server", exist_ok=True)

# Configuration for our local test
LOCAL_SERVER_PORT = 8080
AUTH_URL = f"http://localhost:{LOCAL_SERVER_PORT}/login.html"
APP_URL = f"http://localhost:{LOCAL_SERVER_PORT}/dashboard.html"
USERNAME = "admin"
PASSWORD = "admin123"
SESSION_FILE = "session.json"
OUTPUT_FILE = "product_data.json"

# Create HTML files for our local server
def create_test_html_files():
    """Create HTML files for the local test server."""
    # Login page
    login_html = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login Page</title>
    <style>
       // Variables
$sidebar-bg: #333;
$sidebar-text: white;
$accordion-bg: #444;
$accordion-hover: #555;
$panel-bg: #333;
$link-color: #ddd;
$link-hover: white;
$table-border: #ddd;
$table-header: #f2f2f2;
$button-bg: #4CAF50;
$button-disabled: #ddd;

// Base Styles
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
}

// Sidebar
.sidebar {
  width: 250px;
  background-color: $sidebar-bg;
  height: 100vh;
  color: $sidebar-text;
  padding-top: 20px;
  position: fixed;

  .accordion {
    background-color: $accordion-bg;
    color: $sidebar-text;
    cursor: pointer;
    padding: 18px;
    width: 100%;
    border: none;
    text-align: left;
    outline: none;
    transition: 0.4s;

    &:hover,
    &.active {
      background-color: $accordion-hover;
    }
  }

  .panel {
    padding: 0 18px;
    background-color: $panel-bg;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.2s ease-out;

    a {
      color: $link-color;
      text-decoration: none;
      display: block;
      padding: 10px 0;

      &:hover {
        color: $link-hover;
      }
    }
  }
}

// Main Content
.content {
  margin-left: 250px;
  padding: 20px;
}

// Product Table
.product-table {
  display: none;

  table {
    border-collapse: collapse;
    width: 100%;
    margin-top: 20px;

    th,
    td {
      border: 1px solid $table-border;
      padding: 8px;
      text-align: left;
    }

    th {
      background-color: $table-header;
    }
  }
}

// Pagination
.pagination {
  margin-top: 20px;

  button {
    background-color: $button-bg;
    color: white;
    border: none;
    padding: 8px 16px;
    cursor: pointer;
    margin-right: 5px;

    &:disabled {
      background-color: $button-disabled;
      cursor: not-allowed;
    }
  }
}

    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        <form id="loginForm">
            <input type="text" id="username" name="username" placeholder="Username" required>
            <input type="password" id="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
            <p id="error" class="error">Invalid username or password!</p>
        </form>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            if (username === 'admin' && password === 'admin123') {
                document.cookie = "session=logged_in; path=/";
                window.location.href = 'dashboard.html';
            } else {
                document.getElementById('error').style.display = 'block';
            }
        });
    </script>
</body>
</html>

    """
    
    # Dashboard page
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
            .sidebar { width: 250px; background-color: #333; height: 100vh; color: white; padding-top: 20px; position: fixed; }
            .content { margin-left: 250px; padding: 20px; }
            .accordion { background-color: #444; color: white; cursor: pointer; padding: 18px; width: 100%; border: none; text-align: left; outline: none; transition: 0.4s; }
            .active, .accordion:hover { background-color: #555; }
            .panel { padding: 0 18px; background-color: #333; max-height: 0; overflow: hidden; transition: max-height 0.2s ease-out; }
            .panel a { color: #ddd; text-decoration: none; display: block; padding: 10px 0; }
            .panel a:hover { color: white; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .product-table { display: none; }
            .pagination { margin-top: 20px; }
            .pagination button { background-color: #4CAF50; color: white; border: none; padding: 8px 16px; cursor: pointer; margin-right: 5px; }
            .pagination button:disabled { background-color: #ddd; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <button class="accordion">Dashboard Tools</button>
            <div class="panel">
                <button class="accordion">Data Visualization</button>
                <div class="panel">
                    <button class="accordion">Inventory Management</button>
                    <div class="panel">
                        <a href="#" id="viewProducts">View Product Inventory</a>
                    </div>
                </div>
            </div>
        </div>
        <div class="content">
            <h2>Dashboard</h2>
            <p>Welcome to the admin dashboard. Use the sidebar to navigate.</p>
            
            <div id="productTable" class="product-table">
                <h3>Product Inventory</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Product Name</th>
                            <th>Category</th>
                            <th>Price</th>
                            <th>Stock</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="productData">
                        <!-- Products for page 1 -->
                    </tbody>
                </table>
                <div class="pagination">
                    <button id="prevPage" disabled>Previous</button>
                    <span id="pageInfo">Page 1 of 3</span>
                    <button id="nextPage">Next</button>
                </div>
            </div>
        </div>
        <script>
            // Accordion functionality
            var acc = document.getElementsByClassName("accordion");
            for (var i = 0; i < acc.length; i++) {
                acc[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    var panel = this.nextElementSibling;
                    if (panel.style.maxHeight) {
                        panel.style.maxHeight = null;
                    } else {
                        panel.style.maxHeight = panel.scrollHeight + "px";
                    }
                });
            }
            
            // View products functionality
            document.getElementById("viewProducts").addEventListener("click", function(e) {
                e.preventDefault();
                document.getElementById("productTable").style.display = "block";
                loadProducts(1);
            });
            
            // Product data
            const allProducts = [
                // Page 1
                { id: "P001", name: "Laptop", category: "Electronics", price: "$999.99", stock: "15", status: "In Stock" },
                { id: "P002", name: "Smartphone", category: "Electronics", price: "$699.99", stock: "25", status: "In Stock" },
                { id: "P003", name: "Tablet", category: "Electronics", price: "$349.99", stock: "10", status: "Low Stock" },
                { id: "P004", name: "Headphones", category: "Electronics", price: "$149.99", stock: "30", status: "In Stock" },
                { id: "P005", name: "Monitor", category: "Electronics", price: "$249.99", stock: "8", status: "Low Stock" },
                // Page 2
                { id: "P006", name: "Desk Chair", category: "Furniture", price: "$199.99", stock: "12", status: "In Stock" },
                { id: "P007", name: "Office Desk", category: "Furniture", price: "$299.99", stock: "5", status: "Low Stock" },
                { id: "P008", name: "Bookshelf", category: "Furniture", price: "$149.99", stock: "0", status: "Out of Stock" },
                { id: "P009", name: "Coffee Table", category: "Furniture", price: "$129.99", stock: "7", status: "Low Stock" },
                { id: "P010", name: "Bed Frame", category: "Furniture", price: "$399.99", stock: "3", status: "Low Stock" },
                // Page 3
                { id: "P011", name: "T-Shirt", category: "Clothing", price: "$19.99", stock: "50", status: "In Stock" },
                { id: "P012", name: "Jeans", category: "Clothing", price: "$49.99", stock: "20", status: "In Stock" },
                { id: "P013", name: "Sweater", category: "Clothing", price: "$39.99", stock: "15", status: "In Stock" },
                { id: "P014", name: "Jacket", category: "Clothing", price: "$89.99", stock: "8", status: "Low Stock" },
                { id: "P015", name: "Sneakers", category: "Footwear", price: "$79.99", stock: "12", status: "In Stock" }
            ];

            // Products per page
            const productsPerPage = 5;
            let currentPage = 1;
            const totalPages = Math.ceil(allProducts.length / productsPerPage);
            
            // Load products for a specific page
            function loadProducts(page) {
                currentPage = page;
                const start = (page - 1) * productsPerPage;
                const end = start + productsPerPage;
                const pageProducts = allProducts.slice(start, end);
                
                const tableBody = document.getElementById("productData");
                tableBody.innerHTML = "";
                
                pageProducts.forEach(product => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${product.id}</td>
                        <td>${product.name}</td>
                        <td>${product.category}</td>
                        <td>${product.price}</td>
                        <td>${product.stock}</td>
                        <td>${product.status}</td>
                    `;
                    tableBody.appendChild(row);
                });
                
                // Update pagination controls
                document.getElementById("pageInfo").textContent = `Page ${page} of ${totalPages}`;
                document.getElementById("prevPage").disabled = page === 1;
                document.getElementById("nextPage").disabled = page === totalPages;
            }
            
            // Pagination event listeners
            document.getElementById("prevPage").addEventListener("click", function() {
                if (currentPage > 1) {
                    loadProducts(currentPage - 1);
                }
            });
            
            document.getElementById("nextPage").addEventListener("click", function() {
                if (currentPage < totalPages) {
                    loadProducts(currentPage + 1);
                }
            });
            
            // Check if user is logged in
            function checkLogin() {
                return document.cookie.includes("session=logged_in");
            }
            
            // Redirect to login if not logged in
            if (!checkLogin()) {
                window.location.href = "login.html";
            }
        </script>
    </body>
    </html>
    """
    
    # Write files to the local_server directory
    with open("local_server/login.html", "w") as f:
        f.write(login_html)
    
    with open("local_server/dashboard.html", "w") as f:
        f.write(dashboard_html)

# Create a local server
def start_local_server():
    """Start a local HTTP server to serve our test pages."""
    os.chdir("local_server")
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", LOCAL_SERVER_PORT), handler) as httpd:
        print(f"Serving at http://localhost:{LOCAL_SERVER_PORT}")
        httpd.serve_forever()

# Helper functions for the script
def log_message(message):
    """Print a formatted log message."""
    print(f"[SCRIPT] {message}")

async def check_for_existing_session(page: Page) -> bool:
    """Check if a saved session exists and attempt to use it."""
    if not os.path.exists(SESSION_FILE):
        log_message("No existing session found.")
        return False
    
    try:
        log_message("Found existing session. Attempting to restore...")
        with open(SESSION_FILE, "r") as f:
            storage_state = json.load(f)
        
        # Apply the storage state (cookies)
        await page.context.add_cookies(storage_state["cookies"])
        
        # Test if we can access a protected page
        await page.goto(APP_URL)
        
        # Check if we're logged in by looking for dashboard elements
        try:
            await page.wait_for_selector(".sidebar", timeout=5000)
            log_message("Session restored successfully!")
            return True
        except:
            log_message("Session expired or invalid")
            return False
    except Exception as e:
        log_message(f"Error using saved session: {e}")
        return False

async def authenticate(page: Page) -> bool:
    """Authenticate with the application and save the session."""
    try:
        log_message(f"Navigating to login page: {AUTH_URL}")
        await page.goto(AUTH_URL)
        
        # Wait for the login form to appear
        await page.wait_for_selector("#username", timeout=10000)
        
        log_message("Filling in credentials...")
        # Fill in credentials
        await page.fill("#username", USERNAME)
        await page.fill("#password", PASSWORD)
        
        log_message("Submitting login form...")
        # Click login button and wait for navigation
        await page.click("button[type='submit']")
        
        # Wait for navigation to complete
        try:
            await page.wait_for_selector(".sidebar", timeout=10000)
            
            # Save the session
            log_message("Saving session data...")
            storage_state = await page.context.storage_state()
            with open(SESSION_FILE, "w") as f:
                json.dump(storage_state, f, indent=2)
            
            log_message("Authentication successful!")
            return True
        except TimeoutError:
            log_message("Login unsuccessful - dashboard not found")
            return False
            
    except Exception as e:
        log_message(f"Authentication failed: {e}")
        return False

async def navigate_to_product_table(page: Page) -> bool:
    """Navigate through the UI to reach the product inventory table."""
    try:
        log_message("Navigating to product inventory table...")
        
        # Expand all accordion elements
        accordions = await page.query_selector_all(".accordion")
        for accordion in accordions:
            await accordion.click()
            await page.wait_for_timeout(500)  # Wait for animation
        
        # Click on View Product Inventory
        log_message("Clicking on 'View Product Inventory'...")
        await page.click("#viewProducts")
        
        # Wait for the product table to appear
        await page.wait_for_selector("table", timeout=10000)
        
        log_message("Successfully navigated to product table!")
        return True
    except Exception as e:
        log_message(f"Navigation to product table failed: {e}")
        return False

async def extract_table_data(page: Page) -> list:
    """Extract all product data from the table, handling pagination."""
    all_products = []
    page_number = 1
    
    try:
        log_message("Starting data extraction from product table...")
        
        while True:
            log_message(f"Processing page {page_number}...")
            
            # Wait for table to be fully loaded
            await page.wait_for_selector("table tbody tr", state="visible")
            
            # Extract headers (if first page)
            if not all_products:
                headers = await page.evaluate("""
                    () => {
                        const headerCells = Array.from(document.querySelectorAll('table thead th'));
                        return headerCells.map(cell => cell.textContent.trim());
                    }
                """)
                log_message(f"Found table headers: {headers}")
            
            # Extract current page data
            current_page_data = await page.evaluate("""
                (headers) => {
                    const rows = Array.from(document.querySelectorAll('table tbody tr'));
                    return rows.map(row => {
                        const cells = Array.from(row.querySelectorAll('td'));
                        const rowData = {};
                        cells.forEach((cell, index) => {
                            if (index < headers.length) {
                                rowData[headers[index]] = cell.textContent.trim();
                            }
                        });
                        return rowData;
                    });
                }
            """, headers)
            
            all_products.extend(current_page_data)
            log_message(f"Extracted {len(current_page_data)} products from page {page_number}")
            
            # Check if there's a next page button and if it's enabled
            next_button_disabled = await page.evaluate("""
                () => {
                    const nextButton = document.querySelector('#nextPage');
                    return nextButton && nextButton.disabled;
                }
            """)
            
            if next_button_disabled:
                log_message("No more pages available.")
                break
            
            # Click next page and wait for table to update
            log_message("Navigating to next page...")
            await page.click("#nextPage")
            await page.wait_for_timeout(1000)  # Wait for page transition
            page_number += 1
        
        log_message(f"Total products extracted: {len(all_products)}")
        return all_products
        
    except Exception as e:
        log_message(f"Error extracting table data: {e}")
        if all_products:
            log_message(f"Returning {len(all_products)} products that were extracted before the error")
            return all_products
        return []

async def export_to_json(data: list):
    """Export the harvested data to a JSON file."""
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log_message(f"Data successfully exported to {OUTPUT_FILE}")
    except Exception as e:
        log_message(f"Error exporting data to JSON: {e}")

async def main():
    log_message("Starting product data extraction script...")
    
    # Create HTML files for local testing
    create_test_html_files()
    
    # Start local server in a separate thread
    server_thread = threading.Thread(target=start_local_server, daemon=True)
    server_thread.start()
    log_message(f"Started local test server at http://localhost:{LOCAL_SERVER_PORT}")
    
    # Wait for the server to start
    await asyncio.sleep(1)
    
    # Launch the browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Set to True for production
            slow_mo=100,  # Slow down operations for better visibility
        )
        
        # Create a new context
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        
        try:
            # Check for existing session
            session_valid = await check_for_existing_session(page)
            
            # If no valid session, authenticate
            if not session_valid:
                auth_success = await authenticate(page)
                if not auth_success:
                    log_message("Failed to authenticate. Exiting.")
                    await browser.close()
                    return
            
            # Navigate to product inventory table
            nav_success = await navigate_to_product_table(page)
            if not nav_success:
                log_message("Failed to navigate to product table. Exiting.")
                await browser.close()
                return
            
            # Extract product data
            product_data = await extract_table_data(page)
            
            # Export data to JSON
            if product_data:
                await export_to_json(product_data)
                log_message("Script completed successfully!")
            else:
                log_message("No product data was extracted.")
        
        except Exception as e:
            log_message(f"An unexpected error occurred: {e}")
        
        finally:
            log_message("Closing browser...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())