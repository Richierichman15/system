import { Link } from 'react-router-dom'

export default function MainMenuButton() {
  return (
    <Link to="/" className="menu-button">
      <i className="fas fa-home"></i>
      <span>Main Menu</span>
    </Link>
  )
}
