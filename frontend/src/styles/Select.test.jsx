import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Select } from "./components";

const options = [
  { value: "option1", label: "Option One" },
  { value: "option2", label: "Option Two" },
  { value: "option3", label: "Option Three" },
];

describe("Select", () => {
  it("renders a select element", () => {
    render(<Select options={options} />);
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("renders placeholder as disabled option", () => {
    render(<Select options={options} placeholder="Choose..." />);
    const select = screen.getByRole("combobox");
    const placeholderOption = select.querySelector("option[value='']");
    expect(placeholderOption).toBeInTheDocument();
    expect(placeholderOption).toBeDisabled();
    expect(placeholderOption.textContent).toBe("Choose...");
  });

  it("uses default placeholder when not provided", () => {
    render(<Select options={options} />);
    const select = screen.getByRole("combobox");
    const placeholderOption = select.querySelector("option[value='']");
    expect(placeholderOption.textContent).toBe("Select...");
  });

  it("renders options from array", () => {
    render(<Select options={options} />);
    const select = screen.getByRole("combobox");
    const renderedOptions = select.querySelectorAll("option:not([value=''])");
    expect(renderedOptions).toHaveLength(3);
    expect(renderedOptions[0].textContent).toBe("Option One");
    expect(renderedOptions[1].textContent).toBe("Option Two");
    expect(renderedOptions[2].textContent).toBe("Option Three");
  });

  it("error prop renders error message", () => {
    render(<Select options={options} error="This field is required" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
  });

  it("error prop flips variant to error", () => {
    render(<Select options={options} />);
    const selectNormal = screen.getByRole("combobox");
    expect(selectNormal.className).toContain("border-gray-600");

    render(<Select options={options} error="Error" />);
    const selectError = screen.getAllByRole("combobox")[1];
    expect(selectError.className).toContain("border-red-500");
  });

  it("onChange fires when option selected", () => {
    const handleChange = vi.fn();
    render(<Select options={options} onChange={handleChange} />);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "option2" } });
    expect(handleChange).toHaveBeenCalled();
  });
});
