// Store for registered drugs and company profile
let registeredDrugs = [];
let cart = [];
let companyProfile = null;

// Function to initialize the drug list
function initializeDrugList() {
    // This would typically fetch from a backend
    // For now, we'll use the drugs from localStorage if available
    const storedDrugs = localStorage.getItem('registeredDrugs');
    if (storedDrugs) {
        registeredDrugs = JSON.parse(storedDrugs);
        updateDrugList();
    }
}

// Function to update the drug datalist
function updateDrugList() {
    const drugList = document.getElementById('drug-list');
    drugList.innerHTML = '';
    registeredDrugs.forEach(drug => {
        const option = document.createElement('option');
        option.value = drug.name;
        option.setAttribute('data-price', drug.price);
        drugList.appendChild(option);
    });
}

// Function to update price when drug is selected
function updatePrice() {
    const searchInput = document.getElementById('search-drug');
    const quantityInput = document.getElementById('drug-quantity');
    const priceDisplay = document.getElementById('drug-price');
    
    const selectedDrug = registeredDrugs.find(drug => drug.name === searchInput.value);
    if (selectedDrug) {
        const quantity = parseInt(quantityInput.value) || 0;
        const totalPrice = (selectedDrug.price * quantity).toFixed(2);
        priceDisplay.textContent = totalPrice;
    } else {
        priceDisplay.textContent = '0.00';
    }
}

// Function to add item to cart
function addToCart() {
    const searchInput = document.getElementById('search-drug');
    const quantityInput = document.getElementById('drug-quantity');
    const selectedDrug = registeredDrugs.find(drug => drug.name === searchInput.value);
    
    if (!selectedDrug) {
        alert('Please select a valid drug');
        return;
    }
    
    const quantity = parseInt(quantityInput.value);
    if (!quantity || quantity < 1) {
        alert('Please enter a valid quantity');
        return;
    }
    
    const cartItem = {
        id: Date.now(), // unique ID for the cart item
        name: selectedDrug.name,
        quantity: quantity,
        price: selectedDrug.price,
        total: (selectedDrug.price * quantity)
    };
    
    cart.push(cartItem);
    updateCartDisplay();
    clearForm();
}

// Function to remove item from cart
function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    updateCartDisplay();
}

// Function to update cart display
function updateCartDisplay() {
    const cartContainer = document.getElementById('cart-items');
    const totalAmount = document.getElementById('total-amount');
    
    cartContainer.innerHTML = '';
    let total = 0;
    
    cart.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = 'cart-item';
        itemElement.innerHTML = `
            <div>${item.name}</div>
            <div>${item.quantity}</div>
            <div>₹${item.total.toFixed(2)}</div>
            <button onclick="removeFromCart(${item.id})">×</button>
        `;
        cartContainer.appendChild(itemElement);
        total += item.total;
    });
    
    totalAmount.textContent = total.toFixed(2);
}

// Function to clear the form
function clearForm() {
    document.getElementById('search-drug').value = '';
    document.getElementById('drug-quantity').value = '';
    document.getElementById('drug-price').textContent = '0.00';
}

// Function to handle logo preview
function previewLogo(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('logo-preview-img');
            const placeholder = document.getElementById('logo-placeholder');
            preview.src = e.target.result;
            preview.style.display = 'block';
            placeholder.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
}

// Function to save company profile
async function saveProfile(event) {
    event.preventDefault();
    
    companyProfile = {
        name: document.getElementById('company-name').value,
        address: document.getElementById('company-address').value,
        phone: document.getElementById('company-phone').value,
        email: document.getElementById('company-email').value
    };
    
    // Save to localStorage
    localStorage.setItem('companyProfile', JSON.stringify(companyProfile));
    
    // Show success message
    alert('Profile saved successfully!');
}

// Function to load company profile
function loadCompanyProfile() {
    const savedProfile = localStorage.getItem('companyProfile');
    if (savedProfile) {
        companyProfile = JSON.parse(savedProfile);
        
        // Fill form fields
        document.getElementById('company-name').value = companyProfile.name || '';
        document.getElementById('company-address').value = companyProfile.address || '';
        document.getElementById('company-phone').value = companyProfile.phone || '';
        document.getElementById('company-email').value = companyProfile.email || '';
    }
}

// Function to generate bill HTML
function generateBillHTML(customerName, items, total) {
    if (!companyProfile) {
        alert('Please set up your company profile first!');
        return null;
    }

    const date = new Date().toLocaleDateString();
    const time = new Date().toLocaleTimeString();
    
    return `
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .bill-container { max-width: 800px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; }
                .bill-header { text-align: center; margin-bottom: 20px; }
                .company-info { margin-bottom: 20px; text-align: center; }
                .company-details { margin-bottom: 20px; }
                .customer-info { margin-bottom: 20px; }
                .bill-items { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                .bill-items th, .bill-items td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                .bill-items th { background-color: #f5f5f5; }
                .total { text-align: right; font-weight: bold; }
                .footer { margin-top: 40px; text-align: center; font-size: 0.9em; color: #666; }
            </style>
        </head>
        <body>
            <div class="bill-container">
                <div class="company-info">
                    <h2>${companyProfile.name}</h2>
                    <div class="company-details">
                        <p>${companyProfile.address}</p>
                        <p>Phone: ${companyProfile.phone}</p>
                        <p>Email: ${companyProfile.email}</p>
                    </div>
                </div>
                <div class="bill-header">
                    <h2>Invoice</h2>
                    <p>Date: ${date}</p>
                    <p>Time: ${time}</p>
                </div>
                <div class="customer-info">
                    <p><strong>Customer Name:</strong> ${customerName}</p>
                </div>
                <table class="bill-items">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${items.map(item => `
                            <tr>
                                <td>${item.name}</td>
                                <td>${item.quantity}</td>
                                <td>₹${item.price.toFixed(2)}</td>
                                <td>₹${item.total.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <div class="total">
                    <p>Total Amount: ₹${total.toFixed(2)}</p>
                </div>
                <div class="footer">
                    <p>Thank you for your business!</p>
                    <p>This is a computer-generated invoice.</p>
                </div>
            </div>
        </body>
        </html>
    `;
}

// Function to send email
async function sendEmail(to, subject, htmlContent) {
    try {
        const response = await fetch('https://api.emailjs.com/api/v1.0/email/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                service_id: 'YOUR_EMAILJS_SERVICE_ID', // Replace with your EmailJS service ID
                template_id: 'YOUR_EMAILJS_TEMPLATE_ID', // Replace with your EmailJS template ID
                user_id: 'YOUR_EMAILJS_USER_ID', // Replace with your EmailJS user ID
                template_params: {
                    to_email: to,
                    subject: subject,
                    html_content: htmlContent,
                }
            }),
        });

        if (response.ok) {
            return { success: true };
        } else {
            throw new Error('Failed to send email');
        }
    } catch (error) {
        console.error('Error sending email:', error);
        return { success: false, error: error.message };
    }
}

// Function to generate and send bill
async function generateAndSendBill() {
    const customerName = document.getElementById('customer-name').value;
    const customerEmail = document.getElementById('customer-email').value;

    if (!customerName || !customerEmail) {
        alert('Please enter customer name and email');
        return;
    }

    if (cart.length === 0) {
        alert('Cart is empty');
        return;
    }

    const total = cart.reduce((sum, item) => sum + item.total, 0);
    const billHTML = generateBillHTML(customerName, cart, total);

    // Show loading state
    const generateBillBtn = document.querySelector('.generate-bill-btn');
    const originalBtnText = generateBillBtn.textContent;
    generateBillBtn.textContent = 'Sending...';
    generateBillBtn.disabled = true;

    try {
        const result = await sendEmail(
            customerEmail,
            'Your Bill from Mediconnect Pharmacy',
            billHTML
        );

        if (result.success) {
            // Show success message
            const successDiv = document.createElement('div');
            successDiv.className = 'email-status success';
            successDiv.textContent = 'Bill sent successfully!';
            generateBillBtn.parentNode.appendChild(successDiv);

            // Clear cart and form
            cart = [];
            updateCartDisplay();
            document.getElementById('customer-name').value = '';
            document.getElementById('customer-email').value = '';

            // Remove success message after 3 seconds
            setTimeout(() => {
                successDiv.remove();
            }, 3000);
        } else {
            throw new Error(result.error || 'Failed to send email');
        }
    } catch (error) {
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'email-status error';
        errorDiv.textContent = `Error: ${error.message}`;
        generateBillBtn.parentNode.appendChild(errorDiv);

        // Remove error message after 3 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    } finally {
        // Restore button state
        generateBillBtn.textContent = originalBtnText;
        generateBillBtn.disabled = false;
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    initializeDrugList();
    loadCompanyProfile();
    
    // Add event listeners for price updates
    document.getElementById('search-drug').addEventListener('input', updatePrice);
    document.getElementById('drug-quantity').addEventListener('input', updatePrice);
});

// Function to add a new drug to the registered drugs list (called from register drug form)
function addRegisteredDrug(drugData) {
    registeredDrugs.push(drugData);
    localStorage.setItem('registeredDrugs', JSON.stringify(registeredDrugs));
    updateDrugList();
} 