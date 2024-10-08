import React, { useState, useEffect } from "react";

function Predefined({ onOptionSelect }) {
  return (
    <div>
      <h1>You selected Predefined!</h1>
      <p>Here are some predefined options</p>
      <div className="form-control">
        <label className="label cursor-pointer">
          <span className="label-text">Minimal</span>
          <input
            type="radio"
            name="radio-10"
            className="radio checked:bg-red-500"
            defaultChecked
            onChange={() => onOptionSelect("Minimal")}
          />
        </label>
      </div>
      <div className="form-control">
        <label className="label cursor-pointer">
          <span className="label-text">Standard</span>
          <input
            type="radio"
            name="radio-10"
            className="radio checked:bg-blue-500"
            onChange={() => onOptionSelect("Standard")}
          />
        </label>
      </div>
      <div className="form-control">
        <label className="label cursor-pointer">
          <span className="label-text">RAM-Efficient</span>
          <input
            type="radio"
            name="radio-10"
            className="radio checked:bg-violet-500"
            onChange={() => onOptionSelect("RAM-Efficient")}
          />
        </label>
      </div>
    </div>
  );
}

function Customization({ onCustomizationChange }) {
  return (
    <div>
      <p>Please enter your customization details.</p>
      <textarea 
        className="textarea textarea-bordered" 
        placeholder="Enter customization details"
        onChange={(e) => onCustomizationChange(e.target.value)}
      ></textarea>
    </div>
  );
}

function RecentSubmissions() {
  const [submissions, setSubmissions] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/get-submissions')
      .then(response => response.json())
      .then(data => setSubmissions(data))
      .catch(error => console.error('Error fetching submissions:', error));
  }, []);

  return (
    <div className="mt-8">
      <h2 className="text-2xl mb-4">Recent Submissions</h2>
      <ul>
        {submissions.map(sub => (
          <li key={sub.id} className="mb-2">
            OS: {sub.selected_os}, Option: {sub.option}, Details: {sub.customization_details}
          </li>
        ))}
      </ul>
    </div>
  );
}

function CustomPage() {
  const [selectedOS, setSelectedOS] = useState(null);
  const [selectedOption, setSelectedOption] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [osOptions, setOsOptions] = useState([]);
  const [customizationDetails, setCustomizationDetails] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submissionSuccess, setSubmissionSuccess] = useState(false);

  useEffect(() => {
    fetch('/api/os-options')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        setOsOptions(data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Error fetching OS options:', error);
        setError('Failed to load OS options. Please try again later.');
        setIsLoading(false);
      });
  }, []);
  
  const handleOSSelection = (osId) => {
    setSelectedOS(osId);
  };

  const handleOptionSelection = (option) => {
    setSelectedOption(option);
    setIsDropdownOpen(false);
  };

  const handleSubmit = () => {
    setIsLoading(true);
    const data = {
      selectedOS: selectedOS,
      option: selectedOption,
      customizationDetails: customizationDetails
    };

    fetch('http://127.0.0.1:5000/api/submit-os', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(result => {
        console.log('Success:', result);
        setSubmissionSuccess(true);
        // Reset form
        setSelectedOS(null);
        setSelectedOption("");
        setCustomizationDetails("");
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Error:', error);
        setError('Error submitting OS configuration. Please try again.');
        setIsLoading(false);
      });
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
      <div className="flex flex-col items-center h-screen">
        <div>
          <h1 className="flex justify-center text-3xl p-4">Select Operating System </h1>
          <div className="flex justify-around w-[100vw]">
            <div className="card bg-base-100 w-96 shadow-xl">
              <figure>
                <img
                  src="https://www.unixtutorial.org/images/software/ubuntu-linux.png"
                  alt="Shoes"
                />
              </figure>
              <div className="card-body">
                <h2 className="card-title">Ubuntu</h2>
                <p>Lorem Ipsum is simply dummy text of the printing and typesetting industry. </p>
                <div className="card-actions justify-end">
                  <button className="btn btn-primary">Select</button>
                </div>
              </div>
            </div>
            <div className="card bg-base-100 w-96 shadow-xl">
              <figure>
                <img
                  src="https://colfaxresearch.com/wp-content/uploads/2015/06/archlinux-logo-800x350.jpg"
                  alt="Shoes"
                />
              </figure>
              <div className="card-body">
                <h2 className="card-title">Arch-Linux</h2>
                <p>Lorem Ipsum is simply dummy text of the printing and typesetting industry. </p>
                <div className="card-actions justify-end">
                  <button className="btn btn-primary">Select</button>
                </div>
              </div>
            </div>
          </div>
        </div>

      {/* Dropdown Button */}
      <div className="dropdown mt-4">
        <div
          tabIndex={0}
          role="button"
          className="btn m-1"
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        >
          Options
        </div>

        {/* Conditionally render the dropdown menu */}
        {isDropdownOpen && (
          <ul
            tabIndex={0}
            className="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow"
          >
            <li><a onClick={() => handleOptionSelection("predefined")}>Predefined</a></li>
            <li><a onClick={() => handleOptionSelection("customization")}>Customization</a></li>
          </ul>
        )}
      </div>

      {/* Conditionally render components based on the selection */}
      <div className="mt-6">
        {selectedOption === "predefined" && <Predefined onOptionSelect={setSelectedOption} />}
        {selectedOption === "customization" && <Customization onCustomizationChange={setCustomizationDetails} />}
      </div>

      {/* Submit Button */}
      <button 
        className="btn m-4" 
        onClick={handleSubmit}
        disabled={!selectedOS || !selectedOption || isLoading}
      >
        {isLoading ? 'Submitting...' : 'Submit'}
      </button>

      {submissionSuccess && (
        <div className="alert alert-success">
          OS configuration submitted successfully!
        </div>
      )}

      <RecentSubmissions />
    </div>
  );
}

export default CustomPage;