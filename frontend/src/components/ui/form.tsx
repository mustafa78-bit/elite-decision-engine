import { forwardRef, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { Controller, type Control, type FieldError, type FieldValues, type Path } from "react-hook-form";
import { cn } from "../../lib/utils";

interface FormFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label?: string;
  error?: FieldError;
  children: React.ReactNode;
  className?: string;
}

export function FormField<T extends FieldValues>({
  label,
  error,
  children,
  className,
}: FormFieldProps<T>) {
  return (
    <div className={cn("space-y-1.5", className)}>
      {label && (
        <label className="text-[11px] font-medium text-[var(--text-secondary)] uppercase tracking-[0.06em]">
          {label}
        </label>
      )}
      {children}
      {error && (
        <p className="text-[10px] font-mono text-[var(--accent-red)]">
          {error.message}
        </p>
      )}
    </div>
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const FormInput = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "flex h-9 w-full rounded-lg border bg-[var(--bg-base)] px-3 py-1.5 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-all",
        "border-[var(--border-default)] focus:border-[var(--accent-blue)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-blue)]/30",
        error && "border-[var(--accent-red)] focus:border-[var(--accent-red)] focus:ring-[var(--accent-red)]/30",
        className,
      )}
      {...props}
    />
  ),
);
FormInput.displayName = "FormInput";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

export const FormSelect = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, error, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "flex h-9 w-full rounded-lg border bg-[var(--bg-base)] px-3 py-1.5 text-xs font-mono text-[var(--text-primary)] transition-all",
        "border-[var(--border-default)] focus:border-[var(--accent-blue)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-blue)]/30",
        error && "border-[var(--accent-red)]",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  ),
);
FormSelect.displayName = "FormSelect";

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const FormTextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ className, error, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-20 w-full rounded-lg border bg-[var(--bg-base)] px-3 py-1.5 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-all resize-y",
        "border-[var(--border-default)] focus:border-[var(--accent-blue)] focus:outline-none focus:ring-1 focus:ring-[var(--accent-blue)]/30",
        error && "border-[var(--accent-red)]",
        className,
      )}
      {...props}
    />
  ),
);
FormTextArea.displayName = "FormTextArea";

interface ControlledInputProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label?: string;
  placeholder?: string;
  type?: string;
  className?: string;
}

export function ControlledInput<T extends FieldValues>({
  name,
  control,
  label,
  placeholder,
  type = "text",
  className,
}: ControlledInputProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState }) => (
        <FormField name={name} control={control} label={label} error={fieldState.error}>
          <FormInput
            {...field}
            type={type}
            placeholder={placeholder}
            error={!!fieldState.error}
            className={className}
          />
        </FormField>
      )}
    />
  );
}
