export default function StatusBanner({ health, error }) {
  if (error) {
    return (
      <div 
        className="w-full p-4 flex items-center justify-center"
        style={{ backgroundColor: 'var(--color-error)', color: 'var(--color-on-dark)' }}
      >
        <span className="bmw-body-md">{error}</span>
      </div>
    );
  }

  if (!health) {
    return (
      <div 
        className="w-full p-4 flex items-center justify-center"
        style={{ backgroundColor: 'var(--color-surface-dark-elevated)', color: 'var(--color-on-dark)' }}
      >
        <span className="bmw-body-md">Đang kết nối tới backend...</span>
      </div>
    );
  }

  return null;
}
