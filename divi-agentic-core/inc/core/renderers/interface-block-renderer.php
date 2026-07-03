<?php
/**
 * Interface: Block Renderer
 *
 * Defines the contract for all layout renderers used by Layout_Engine.
 *
 * @package Divi_Agentic_Core
 */

namespace Divi_Agentic_Core\Core\Renderers;

/**
 * Interface Block_Renderer_Interface
 *
 * Cada renderer implementa la logica especifica de un namespace o familia de bloques.
 * El dispatcher de Layout_Engine resuelve el renderer apropiado y aplica post-proceso.
 */
interface Block_Renderer_Interface {

	/**
	 * Render a block schema into a serializable attribute array.
	 *
	 * @param string $slug          Resolved block slug (e.g. divi/text, dgpc/product-carousel).
	 * @param array  $data         Raw block data from the page definition schema.
	 * @param string $content_key  Inner content key for children rendering (passed through; renderer may ignore).
	 * @param string $children_html Pre-rendered HTML of child blocks.
	 *
	 * @return array{
	 *     attrs: array<string, mixed>,
	 *     inner: string,
	 *     inner_html: string
	 * }
	 */
	public function render( string $slug, array $data, string $content_key, string $children_html ): array;
}
