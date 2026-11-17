/**
 * Structify mark: a drawing sheet holding a small tree diagram.
 * One node (the root, in signal orange) fans out to two children, which is
 * what the product does to a document. Uses currentColor so it follows the theme.
 */
export default function LogoMark({
  size = 32,
  title = "Structify logo",
  className,
}: {
  size?: number;
  title?: string;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label={title}
      className={className}
      fill="none"
    >
      <rect x="2" y="2" width="60" height="60" stroke="currentColor" strokeWidth="4" />
      <path d="M32 24V34M16 34H48M16 34V42M48 34V42" stroke="currentColor" strokeWidth="4" />
      <rect x="25" y="10" width="14" height="14" fill="var(--signal, #ff4a1c)" />
      <rect x="9" y="42" width="14" height="14" fill="currentColor" />
      <rect x="41" y="42" width="14" height="14" fill="currentColor" />
    </svg>
  );
}
