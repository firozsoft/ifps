'use strict';

// Function to generate HTML for an alert element
const Alert = (status, message) => `
  <div data-mdb-alert-init="" class="alert alert-${ status }" role="alert" data-mdb-color="${ status }" data-mdb-alert-initialized="true">
    ${ message }
  </div>
`;

// DOM elements
const responseContainer = document.getElementById('response-container');
const spinner = document.getElementById('spinner-container');
const fplSubmissionForm = document.getElementById('fpl-submission-form');
const submitButton = document.getElementById('submit-button');
const resetButton = document.getElementById('reset-button');

// Event listener for form submission
fplSubmissionForm.addEventListener('submit', async function (event) {
  event.preventDefault();

  // Disable buttons and show spinner
  toggleFormState(true);

  const formData = new FormData(fplSubmissionForm);

  try {
    const response = await fetch(fplSubmissionForm.action, {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    renderResponse(data);
  } catch (error) {
    console.error('Fetch error or server error:', String(error));
    renderResponse({ 'Error(s)': 'An error occurred while processing the request.' });
  } finally {
    // Re-enable buttons and hide spinner
    toggleFormState(false);
  }
});

// Function to toggle form state (disable/enable buttons and spinner visibility)
function toggleFormState (isDisabled) {
  submitButton.disabled = isDisabled;
  resetButton.disabled = isDisabled;
  spinner.classList.toggle('d-none', !isDisabled);
  responseContainer.classList.toggle('d-none', isDisabled);
}

// Function to render response data
function renderResponse (data) {
  if (!data) return;

  let content = ''; // String to accumulate HTML
  let status = 'success';

  // Determine response status
  if (data[ 'Error(s)' ]) {
    status = 'danger';
  } else if (data[ 'NOTAM(s)' ]) {
    status = 'warning';
  }

  // Handle success or other statuses
  if (status === 'success') {
    content = Alert(status, data.Success || 'Operation completed successfully.');
  } else {
    content = renderAlerts(data);
  }

  responseContainer.innerHTML = content;
}

// Function to render alerts for error or warning statuses
function renderAlerts (data) {
  let content = '';

  Object.entries(data).forEach(([ key, value ]) => {
    const alertStatus = key === 'Error(s)' ? 'danger' : 'warning';

    if (key === 'NOTAM(s)') {
      content += '<hr class="text-black-50" />';
    }
    content += `<h3>${ key }</h3>`;

    // Handle nested objects or plain values
    if (typeof value === 'object' && value !== null) {
      for (const nestedValue of Object.values(value)) {
        content += Alert(alertStatus, nestedValue);
      }
    } else {
      content += Alert(alertStatus, value);
    }
  });

  return content;
}
