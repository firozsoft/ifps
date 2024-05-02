'use strict';

// Function to generate HTML for an alert element
const Alert = (status, message) => `
  <div data-mdb-alert-init="" class="alert alert-${ status }" role="alert" data-mdb-color="${ status }" data-mdb-alert-initialized="true">
    ${ message }
  </div>
`;

// DOM element to display response alerts
const responseContainer = document.getElementById('response-container');

// DOM element for the spinner element
const spinner = document.getElementById('spinner-container');

// DOM element for the form
const fplSubmissionForm = document.getElementById('fpl-submission-form');

// DOM element for the form's submit button
const submitButton = document.getElementById('submit-button');

// DOM element for the form's reset button
const resetButton = document.getElementById('reset-button');

// Attach an event handler to the form's submit event
fplSubmissionForm.addEventListener('submit', async function (event) {
  // Prevent the default form submission behavior
  event.preventDefault();

  // Disable the submit button to prevent multiple submissions
  submitButton.disabled = true;
  // Disable the reset button to prevent multiple submissions
  resetButton.disabled = true;

  // Show spinner
  spinner.classList.remove("d-none");
  // Hide the responseContainer
  responseContainer.classList.add("d-none");

  // Create a new FormData object to collect form data
  const formData = new FormData(fplSubmissionForm);

  // Convert FormData object to a plain object for easier handling
  const formDataObject = {};
  formData.forEach((value, key) => {
    formDataObject[ key ] = value;
  });

  try {
    // Submit the form data using fetch
    const response = await fetch(fplSubmissionForm.action, {
      method: 'POST',
      body: formData
    });

    // Parse the response body as JSON
    const data = await response.json();

    // Handle successful response
    renderResponse(data);
  } catch (error) {
    // Handle fetch error or server error
    console.error('Fetch error or server error:', error);
    renderResponse({ 'Error(s)': 'An error occurred while processing the request.' });
  } finally {
    // Re-enable the submit button after fetch completes (whether it succeeds or fails)
    submitButton.disabled = false;
    // Re-enable the reset button after fetch completes (whether it succeeds or fails)
    resetButton.disabled = false;
    // Hide the spinner
    spinner.classList.add("d-none");
    // Show the responseContainer
    responseContainer.classList.remove("d-none");
  }
});

// Function to render response data in HTML elements
function renderResponse (data) {
  if (!data) {
    return;
  }

  // Clear previous content in the response container
  responseContainer.innerHTML = '';

  let status = 'success'; // Default status

  // Determine the status based on the response data properties
  if (data.hasOwnProperty('Error(s)')) {
    status = 'danger';
  } else if (data.hasOwnProperty('NOTAM(s)')) {
    status = 'warning';
  }

  // Check the status to determine how to render the response
  if (status === 'success') {
    // Render a single success alert
    const successAlert = Alert(status, data.Success);
    responseContainer.innerHTML = successAlert;
  } else {
    // Render multiple error/warning alerts if data contains any errors/warnings

    // Iterate over the properties of the data object
    Object.entries(data).forEach(([ key, value ]) => {
      // Determine the status based on the key
      const alertStatus = key === 'Error(s)' ? 'danger' : 'warning';

      if (key === 'NOTAM(s)') {
        responseContainer.innerHTML += `<hr class="text-black-50" />`;
      }
      responseContainer.innerHTML += `<h3>${ key }</h3>`;

      if (typeof value === 'object' && value !== null) {
        // If the value is an object (nested object), iterate over its values
        for (const nestedValue of Object.values(value)) {
          const alert = Alert(alertStatus, nestedValue);
          responseContainer.innerHTML += alert; // Append alert
        }
      } else {
        // If the value is not an object, directly render an alert for the value
        const alert = Alert(alertStatus, value);
        responseContainer.innerHTML += alert; // Append alert
      }
    });
  }
}
