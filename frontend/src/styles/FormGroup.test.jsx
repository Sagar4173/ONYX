import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FormGroup, FormLabel, FormHint, FormError } from "../components/ui/StyleComponents";

describe("FormGroup", () => {
  it("FormGroup renders children", () => {
    render(
      <FormGroup>
        <input data-testid="child" />
      </FormGroup>
    );
    expect(screen.getByTestId("child")).toBeInTheDocument();
  });

  it("FormLabel renders label text", () => {
    render(<FormLabel>Email</FormLabel>);
    expect(screen.getByText("Email")).toBeInTheDocument();
  });

  it("FormLabel renders required asterisk when required is true", () => {
    const { container } = render(<FormLabel required>Name</FormLabel>);
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(container.querySelector("span")).toHaveTextContent("*");
  });

  it("FormLabel does not render asterisk when required is false", () => {
    const { container } = render(<FormLabel>Name</FormLabel>);
    expect(container.querySelector("span")).not.toBeInTheDocument();
  });

  it("FormHint renders hint text", () => {
    render(<FormHint>Enter your full name</FormHint>);
    expect(screen.getByText("Enter your full name")).toBeInTheDocument();
  });

  it("FormError renders error text", () => {
    render(<FormError>This field is required</FormError>);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
  });
});
