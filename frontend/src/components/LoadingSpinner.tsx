// frontend/src/components/LoadingSpinner.tsx
export default function LoadingSpinner({
  size = 40,
  color = "border-blue-500",
}: {
  size?: number;
  color?: string;
}) {
  return (
    <div
      className="flex justify-center items-center w-full py-8"
      role="status"
      aria-live="polite"
    >
      <div
        style={{width: size, height: size}}
        className={`border-4 ${color} border-t-transparent rounded-full animate-spin`}
      />
    </div>
  );
}
